import json
import pprint
from datetime import timedelta
from time import sleep
from unittest import mock

import responses
from django.utils import timezone
from rest_framework.renderers import JSONRenderer
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from kw_webapp import constants
from kw_webapp.constants import WkSrsLevel, WANIKANI_SRS_LEVELS
from kw_webapp.models import Level, Report, Announcement, Vocabulary, MeaningSynonym, AnswerSynonym
from kw_webapp.tasks import get_vocab_by_kanji, sync_with_wk
from kw_webapp.tests.utils import create_user, create_profile, create_vocab, create_reading, create_userspecific, \
    create_review_for_specific_time, mock_vocab_list_response_with_single_vocabulary, mock_user_info_response
from kw_webapp.utils import one_time_orphaned_level_clear


class TestProfileApi(APITestCase):

    def prepare_admin(self):
        self.admin = create_user("admin")
        create_profile(self.admin, "any_key", 5)
        self.admin.is_staff = True
        self.admin.save()

    def setUp(self):
        self.prepare_admin()
        self.user = create_user("Tadgh")
        create_profile(self.user, "any_key", 5)
        self.vocabulary = create_vocab("radioactive bat")
        self.reading = create_reading(self.vocabulary, "ねこ", "猫", 5)
        self.review = create_userspecific(self.vocabulary, self.user)

    def test_profile_contains_correct_within_day_or_hour_counts(self):
        self.client.force_login(user=self.user)
        self.review.answered_correctly(True)
        self.review.save()

        response = self.client.get(reverse("api:user-me"))
        self.assertEqual(response.data['profile']['reviews_within_hour_count'], 0)
        self.assertEqual(response.data['profile']['reviews_within_day_count'], 1)

    def test_profile_contains_expected_fields(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("api:user-me"))
        data = response.data['profile']

        # Ensure new 2.0 fields are all there
        self.assertIsNotNone(data['auto_advance_on_success_delay_milliseconds'])
        self.assertIsNotNone(data['use_eijiro_pro_link'])
        self.assertIsNotNone(data['show_kanji_svg_stroke_order'])
        self.assertIsNotNone(data['show_kanji_svg_grid'])
        self.assertIsNotNone(data['kanji_svg_draw_speed'])

    def test_preprocessor_future_reviews_counts_correctly_provides_same_day_review_count(self):
        create_review_for_specific_time(self.user, "some word", timezone.now() + timedelta(minutes=30))
        create_review_for_specific_time(self.user, "some word", timezone.now() + timedelta(hours=12))
        create_review_for_specific_time(self.user, "some word", timezone.now() + timedelta(hours=48))

        self.client.force_login(user=self.user)
        response = self.client.get(reverse("api:user-me"))

        self.assertEqual(response.data["profile"]['reviews_within_day_count'], 2)
        self.assertEqual(response.data["profile"]['reviews_within_hour_count'], 1)
        self.assertEqual(response.data["profile"]['reviews_count'], 1)

    def test_future_review_counts_preprocessor_does_not_include_currently_active_reviews(self):
        within_day_review = create_review_for_specific_time(self.user, "some word",
                                                            timezone.now() + timedelta(hours=12))
        within_day_review.needs_review = True
        within_day_review.save()

        self.client.force_login(user=self.user)
        response = self.client.get(reverse("api:user-me"))

        self.assertEqual(response.data["profile"]['reviews_within_day_count'], 0)
        self.assertEqual(response.data["profile"]['reviews_within_hour_count'], 0)
        self.assertEqual(response.data["profile"]['reviews_count'], 2)

    def test_review_count_preprocessor_returns_sane_values_when_user_has_no_vocabulary_unlocked(self):
        self.review.delete()

        self.client.force_login(user=self.user)
        response = self.client.get(reverse("api:user-me"))

        self.assertEqual(response.data["profile"]['reviews_within_day_count'], 0)
        self.assertEqual(response.data["profile"]['reviews_within_hour_count'], 0)
        self.assertEqual(response.data["profile"]['reviews_count'], 0)

    def test_preprocessor_srs_counts_are_correct(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse("api:user-me"))

        self.assertEqual(response.data['profile']['srs_counts']['apprentice'], 1)
        self.assertEqual(response.data['profile']['srs_counts']['guru'], 0)
        self.assertEqual(response.data['profile']['srs_counts']['master'], 0)
        self.assertEqual(response.data['profile']['srs_counts']['enlightened'], 0)
        self.assertEqual(response.data['profile']['srs_counts']['burned'], 0)

    def test_updating_profile_triggers_srs_correctly(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse("api:user-me"))

        self.assertEqual(response.data['profile']['srs_counts']['apprentice'], 1)
        self.assertEqual(response.data['profile']['srs_counts']['guru'], 0)
        self.assertEqual(response.data['profile']['srs_counts']['master'], 0)
        self.assertEqual(response.data['profile']['srs_counts']['enlightened'], 0)
        self.assertEqual(response.data['profile']['srs_counts']['burned'], 0)
        user_dict = dict(response.data)
        user_dict['profile']['on_vacation'] = True
        user_dict['profile']['follow_me'] = True

    # self.client.put(reverse("api:profile-detail", (self.user.profile.id,)), user_dict, format='json')

    def test_locking_current_level_disables_following_setting(self):
        self.client.force_login(user=self.user)
        self.user.profile.follow_me = True
        self.user.profile.level = 5
        self.user.save()

        self.client.post(reverse("api:level-lock", args=(self.user.profile.level,)))
        response = self.client.get(reverse("api:user-me"))
        self.assertFalse(response.data["profile"]["follow_me"])

    def test_nonexistent_user_specific_id_raises_error_in_record_answer(self):
        self.client.force_login(user=self.user)
        non_existent_review_id = 9999

        response = self.client.post(reverse("api:review-correct", args=(non_existent_review_id,)),
                                    data={'wrong_before': 'false'})

        self.assertEqual(response.status_code, 404)

    def test_locking_a_level_locks_successfully(self):
        self.client.force_login(user=self.user)
        response = self.client.post(reverse("api:level-lock", args=(self.user.profile.level,)))

        self.assertEqual(response.data["locked"], 1)

    def test_filtering_on_wk_srs_levels_works(self):
        self.client.force_login(user=self.user)
        word = create_vocab("phlange")
        self.user.profile.minimum_wk_srs_level_to_review = WkSrsLevel.BURNED.name
        self.user.profile.save()
        another_review = create_userspecific(word, self.user)
        another_review.wanikani_srs_numeric = WANIKANI_SRS_LEVELS[WkSrsLevel.BURNED.name][0]
        another_review.save()

        response = self.client.get(reverse("api:review-current"))

        self.assertNotContains(response, "radioactive bat")
        self.assertContains(response, "phlange")

    def test_review_page_shows_all_items_when_burnt_setting_is_disabled(self):
        self.client.force_login(user=self.user)
        word = create_vocab("phlange")
        self.user.profile.minimum_wk_srs_level_to_review = WkSrsLevel.APPRENTICE.name
        self.user.profile.save()
        another_review = create_userspecific(word, self.user)
        another_review.wanikani_srs_numeric = 5
        another_review.save()

        response = self.client.get(reverse("api:review-current"))

        self.assertContains(response, "radioactive bat")
        self.assertContains(response, "phlange")

    def test_recording_answer_works_on_correct_answer(self):
        self.client.force_login(user=self.user)

        self.client.post(reverse("api:review-correct", args=(self.review.id,)), data={"wrong_before": "false"})
        self.review.refresh_from_db()

        self.assertEqual(self.review.correct, 1)
        self.assertTrue(self.review.streak == 2)
        self.assertFalse(self.review.needs_review)

    def test_wrong_answer_records_failure(self):
        self.client.force_login(user=self.user)

        self.client.post(reverse("api:review-incorrect", args=(self.review.id,)))
        self.review.refresh_from_db()

        self.assertTrue(self.review.incorrect == 1)
        self.assertTrue(self.review.correct == 0)
        self.assertTrue(self.review.streak == 1)
        self.assertTrue(self.review.needs_review)

    def test_review_requires_login(self):
        response = self.client.get(reverse("api:review-current"))
        self.assertEqual(response.status_code, 401)

    def test_user_unlocking_too_high_level_fails(self):
        self.client.force_login(user=self.user)
        self.user.profile.level = 5
        self.user.save()
        level_too_high = 20

        response = self.client.post(reverse("api:level-unlock", args=(level_too_high,)))
        self.assertEqual(response.status_code, 403)

    @mock.patch("api.views.unlock_eligible_vocab_from_levels", side_effect=lambda x, y: [1, 0, 0])
    def test_unlocking_a_level_unlocks_all_vocab(self, garbage):
        self.client.force_login(user=self.user)
        self.user.profile.api_valid = True
        self.user.profile.save()
        s1 = reverse("api:level-unlock", args=(5,))
        response = self.client.post(s1)
        self.assertEqual(response.data['unlocked_now'], 1)

    def test_burnt_items_arent_included_when_getting_next_review_date(self):
        self.client.force_login(user=self.user)
        current_time = timezone.now()
        self.review.next_review_date = current_time
        self.review.needs_review = False
        self.review.save()

        older_burnt_review = create_userspecific(create_vocab("test"), self.user)
        older_burnt_review.burned = True
        older_burnt_review.needs_review = False
        an_hour_ago = current_time - timedelta(hours=1)
        older_burnt_review.next_review_date = an_hour_ago
        older_burnt_review.save()

        response = self.client.get(reverse("api:user-me"))

        self.assertEqual(response.data['profile']['next_review_date'], current_time)

    def test_adding_synonym_adds_synonym(self):
        self.client.force_login(user=self.user)
        synonym_kana = "いぬ"
        synonym_kanji = "犬"
        s1 = reverse("api:reading-synonym-list")
        response = self.client.get(s1)
        self.assertEqual(response.data['count'], 0)

        response = self.client.post(s1, data={"review": self.review.id,
                                              "kana": synonym_kana,
                                              "character": synonym_kanji})

        self.review.refresh_from_db()
        found_synonym = self.review.reading_synonyms.first()

        self.assertTrue(synonym_kana in self.review.reading_synonyms_list())
        self.assertEqual(found_synonym.kana, synonym_kana)
        self.assertEqual(found_synonym.character, synonym_kanji)

    def test_lesson_route_returns_srs_0_reviews(self):
        self.client.force_login(user=self.user)

        # Create a lesson
        new_review = create_userspecific(create_vocab("sample"), self.user)
        new_review.streak = 0
        new_review.save()

        response = self.client.get(reverse("api:review-lesson"))
        self.assertEqual(response.data["count"], 1)

    def test_reviews_endpoint_omits_lessons(self):
        self.client.force_login(user=self.user)

        # Create a lesson
        new_review = create_userspecific(create_vocab("sample"), self.user)
        new_review.streak = 0
        new_review.save()

        response = self.client.get(reverse("api:review-current"))
        self.assertEqual(response.data["count"], 1)

    def test_user_getting_answer_wrong_cannot_drop_below_1_in_reviews(self):
        self.client.force_login(user=self.user)
        self.review.streak = 1
        self.review.save()

        self.client.post(reverse("api:review-incorrect", args=(self.review.id,)))
        self.review.refresh_from_db()
        self.assertEqual(self.review.streak, 1)

    def test_once_user_answers_lesson_once_it_becomes_review(self):
        self.client.force_login(user=self.user)

        # Create a lesson
        new_review = create_userspecific(create_vocab("sample"), self.user)
        new_review.streak = 0
        new_review.save()

        response = self.client.get(reverse("api:review-lesson"))
        self.assertEqual(response.data["count"], 1)

        self.client.post(reverse("api:review-correct", args=(new_review.id,)))
        self.review.refresh_from_db()

        response = self.client.get(reverse("api:review-lesson"))
        self.assertEqual(response.data["count"], 0)

    def test_vocabulary_view_returns_related_review_id_if_present(self):
        self.client.force_login(user=self.user)

        response = self.client.get(reverse("api:vocabulary-detail", args=(self.review.vocabulary.id,)))

        self.assertEqual(response.data['review'], self.review.id)

    def test_review_views_nested_vocabulary_omits_review_field(self):
        self.client.force_login(user=self.user)

        response = self.client.get(reverse("api:review-detail", args=(self.review.id,)))

        self.assertTrue('review' not in response.data['vocabulary'])

    def test_profile_serializer_gets_correct_srs_counts(self):
        review1 = create_review_for_specific_time(self.user, "guru", timezone.now()+ timedelta(hours=12))
        review1.streak = 4
        review1.save()
        review2 = create_review_for_specific_time(self.user, "appren1", timezone.now()+ timedelta(hours=12))
        review2.streak = 3
        review2.save()
        review3 = create_review_for_specific_time(self.user, "appren2", timezone.now()+ timedelta(hours=12))
        review3.streak = 3
        review3.save()

        self.client.force_login(user=self.user)
        response = self.client.get(reverse("api:user-me"))

    @responses.activate
    def test_adding_a_level_to_reset_command_only_resets_levels_above_or_equal_togiven(self):
        self.client.force_login(user=self.user)
        v = create_vocab("test")
        create_reading(v, "test", "test", 3)
        create_userspecific(v, self.user)
        mock_user_info_response(self.user.profile.api_key)

        self.user.profile.unlocked_levels.get_or_create(level=2)
        response = self.client.get((reverse("api:review-current")))
        self.assertEqual(response.data['count'], 2)
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [5,2])
        self.client.post(reverse("api:user-reset"), data={'level': 3})

        response = self.client.get((reverse("api:review-current")))
        self.assertEqual(response.data['count'], 0)
        self.assertListEqual(self.user.profile.unlocked_levels_list(), [2])

    def test_locking_a_level_successfully_clears_the_level_object(self):
        self.client.force_login(user=self.user)
        level = Level.objects.get(profile=self.user.profile, level=5)
        self.assertTrue(level is not None)

        self.client.post(reverse("api:level-lock", args=(self.user.profile.level,)))

        levels = Level.objects.filter(profile=self.user.profile, level=5)
        self.assertEqual(levels.count(), 0)


    def test_one_time_orphan_clear_deletes_orphaned_levels(self):
        l5 = self.user.profile.unlocked_levels.get_or_create(level=5)[0]
        l6 = self.user.profile.unlocked_levels.get_or_create(level=6)[0]
        l7 = self.user.profile.unlocked_levels.get_or_create(level=7)[0]
        l8 = self.user.profile.unlocked_levels.get_or_create(level=8)[0]
        l9 = self.user.profile.unlocked_levels.get_or_create(level=9)[0]

        level_count = Level.objects.filter(profile=self.user.profile).count()
        self.assertEqual(level_count, 5)

        self.user.profile.unlocked_levels.remove(l6)
        self.user.profile.unlocked_levels.remove(l7)

        #Oh no two orphaned levels.
        level_count = Level.objects.filter(profile=None).count()
        self.assertEqual(level_count, 2)

        one_time_orphaned_level_clear()

        # Our user has the correct amount of levels associated..
        level_count = Level.objects.filter(profile=self.user.profile).count()
        self.assertEqual(len(self.user.profile.unlocked_levels_list()), 3)

        # No more orphaned levels!
        level_count = Level.objects.filter(profile=None).count()
        self.assertEqual(level_count, 0)

    def test_reporting_vocab_creates_report(self):
        self.client.force_login(user=self.user)

        self.client.post(reverse("api:report-list"), data={"reading": self.reading.id, "reason": "This makes no sense!!!"})

        reports = Report.objects.all()

        self.assertEqual(reports.count(), 1)
        report = reports[0]
        self.client.delete(reverse("api:report-detail", args=(report.id,)))
        self.assertEqual(report.reading, self.reading)
        self.assertEqual(report.created_by, self.user)
        self.assertLessEqual(report.created_at, timezone.now())

    def test_report_counts_endpoint(self):
        # Report a vocab.
        self.client.force_login(user=self.user)
        # This should only ever create ONE report, as we continually update the same one. We do not allow users to
        # multi-report a single vocab.
        self.client.post(reverse("api:report-list"), data={"reading": self.reading.id, "reason": "This still makes no sense!!!"})
        self.client.post(reverse("api:report-list"), data={"reading": self.reading.id, "reason": "ahhh!!!"})
        self.client.post(reverse("api:report-list"), data={"reading": self.reading.id, "reason": "Help!"})
        self.client.post(reverse("api:report-list"), data={"reading": self.reading.id, "reason": "asdf!!!"})
        self.client.post(reverse("api:report-list"), data={"reading": self.reading.id, "reason": "fdsa!!!"})
        self.client.post(reverse("api:report-list"), data={"reading": self.reading.id, "reason": "Final report!!!!"})

        # Have another user report it
        user = create_user("test2")
        create_profile(user, "test", 5)
        self.client.force_login(user=user)
        self.client.post(reverse("api:report-list"), data={"reading": self.reading.id, "reason": "This still makes no sense!!!"})

        # Report another vocab, but only once
        new_vocab = create_vocab("some other vocab")
        reading = create_reading(new_vocab, "reading", "reading_char", 1)

        self.client.post(reverse("api:report-list"), data={"reading": reading.id, "reason": "This still makes no sense!!!"})

        # Login with admin
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("api:report-counts"))

        assert(resp.data[0]["report_count"] > resp.data[1]["report_count"])

        assert(resp.data[0]["report_count"] == 2)
        assert(resp.data[0]['reading'] == self.reading.id)

        assert(resp.data[1]["report_count"] == 1)
        assert(resp.data[1]['reading'] == reading.id)

        resp = self.client.get(reverse("api:report-list"))
        assert(resp.data["count"] == 3)

    def test_ordering_on_announcements_works(self):

        Announcement.objects.create(creator=self.user, title="ASD123", body="ASDSAD")
        sleep(1)
        Announcement.objects.create(creator=self.user, title="ASD1234", body="ASDSAD")
        sleep(1)
        Announcement.objects.create(creator=self.user, title="ASD1345", body="ASDSAD")
        sleep(1)
        Announcement.objects.create(creator=self.user, title="ASD123456", body="ASDSAD")
        sleep(1)

        response = self.client.get(reverse("api:announcement-list"))

        announcements = response.data['results']
        self.assertGreater(announcements[0]['pub_date'], announcements[1]['pub_date'])
        self.assertGreater(announcements[1]['pub_date'], announcements[2]['pub_date'])
        self.assertGreater(announcements[2]['pub_date'], announcements[3]['pub_date'])

    def test_get_vocab_by_kanji_works_in_case_of_multiple_reading_vocab(self):
        v = create_vocab("my vocab")
        create_reading(v, "kana_1", "kanji", 5)
        create_reading(v, "kana_2", "kanji", 5)
        get_vocab_by_kanji("kanji")

    def test_review_serializer_shows_both_reading_and_reading_synonyms(self):
        self.client.force_login(self.user)
        meaning_synonym = "Wow a meaning synonym!"
        reading_synonym_kana = "kana"
        reading_synonym_character = "character"

        MeaningSynonym.objects.create(review=self.review, text=meaning_synonym)
        AnswerSynonym.objects.create(review=self.review, kana=reading_synonym_kana, character=reading_synonym_character)

        self.review.refresh_from_db()

        assert(len(self.review.meaning_synonyms.all()) > 0)
        assert(len(self.review.reading_synonyms.all()) > 0)
        response = self.client.get(reverse("api:review-detail", args=(self.review.id,)))
        data = response.data
        assert(data['meaning_synonyms'][0]['text'] == meaning_synonym)
        assert(data['reading_synonyms'][0]['kana'] == reading_synonym_kana)
        assert(data['reading_synonyms'][0]['character'] == reading_synonym_character)

        response = self.client.get(reverse("api:review-current"))
        data = response.data
        assert(data['results'][0]['meaning_synonyms'][0]['text'] == meaning_synonym)
        assert(data['results'][0]['reading_synonyms'][0]['character'] == reading_synonym_character)
        assert(data['results'][0]['reading_synonyms'][0]['kana'] == reading_synonym_kana)

        response = self.client.get(reverse("api:review-current"))
        data = response.data
        assert(data['results'][0]['meaning_synonyms'][0]['text'] == meaning_synonym)
        assert(data['results'][0]['reading_synonyms'][0]['character'] == reading_synonym_character)
        assert(data['results'][0]['reading_synonyms'][0]['kana'] == reading_synonym_kana)

    def test_get_vocab_by_kanji_correctly_fails_on_duplicate_kanji(self):
        v = create_vocab("my vocab")
        create_reading(v, "kana_1", "kanji", 5)
        v2 = create_vocab("my vocab")
        create_reading(v2, "kana_2", "kanji", 5)

        self.assertRaises(Vocabulary.MultipleObjectsReturned, get_vocab_by_kanji, "kanji")

    def test_fetching_vocabulary_shows_is_reviable_field_on_associated_vocabulary(self):
        self.client.force_login(self.user)

        self.review.wanikani_srs_numeric = 1
        self.review.save()

        wk_burned_review = create_userspecific(create_vocab("test"), self.user)
        wk_burned_review.wanikani_srs_numeric = 9
        wk_burned_review.save()

        self.user.profile.minimum_wk_srs_level_to_review = WkSrsLevel.BURNED.name
        self.user.profile.save()
        # TODO set my default vocab review to burned.
        # TODO ensure that the `is_reviewable` is false on first, true on second.
        response = self.client.get(reverse("api:vocabulary-list"))
        data = response.data

        assert(data['results'][0]['is_reviewable'] is False)
        assert(data['results'][1]['is_reviewable'] is True)

    def test_users_with_invalid_api_keys_correctly_get_their_flag_changed_in_profile(self):
        self.user.profile.api_key = "ABC123"
        self.user.profile.api_valid = True
        self.user.profile.save()

        sync_with_wk(self.user.id)

        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.api_valid)

    def test_meaning_contains_checks_for_word_boundaries(self):
        self.client.force_login(self.user)
        create_vocab("frog")
        create_vocab("puppy")
        create_vocab("up, upwards")
        create_vocab("not down, up")

        response = self.client.get(reverse("api:vocabulary-list") + "?meaning_contains=up")
        data = response.data
        assert(len(data['results']) == 2)

    def test_sending_patch_to_profile_correctly_updates_information(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("api:profile-list"))
        data = response.data
        id = data['results'][0]['id']
        self.client.patch(reverse("api:profile-detail", args=(id,)), data={'on_vacation': True}, format='json')
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        assert(self.user.profile.vacation_date is not None)

    def test_sending_put_to_profile_correctly_updates_information(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("api:profile-list"))
        data = response.data
        id = data['results'][0]['id']
        request = data['results'][0]
        request['on_vacation'] = True
        response = self.client.put(reverse("api:profile-detail", args=(id,)), data=request, format='json')
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        assert(self.user.profile.vacation_date is not None)
        data = response.data
        assert(data is not None)

    def test_enable_follow_me_syncs_user_immediately(self):
        # Given
        self.client.force_login(self.user)
        self.user.profile.follow_me = False
        self.user.profile.save()
        response = self.client.get(reverse("api:profile-list"))
        data = response.data
        id = data['results'][0]['id']

        # When
        self.client.patch(reverse("api:profile-detail", args=(id,)), data={'follow_me': True}, format='json')

        # Then
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        assert(self.user.profile.follow_me is True)

    def test_attempting_to_sync_with_invalid_api_key_sets_correct_profile_value(self):
        # Given
        self.client.force_login(self.user)
        self.user.profile.api_key = "Some Garbage"
        self.user.profile.save()

        # When
        self.client.post(reverse("api:user-sync"))

        # Then
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        assert(self.user.profile.api_valid is False)

    def test_correct_does_not_increment_upon_lesson_completion(self):
        # Given
        self.client.force_login(self.user)
        self.review.streak = 0
        self.review.save()

        # When
        self.client.post(reverse("api:review-correct", args=(self.review.id,)))

        # Then
        response = self.client.get(reverse("api:review-detail", args=(self.review.id,)))
        review = response.data
        self.assertEqual(review['correct'], 0)
        self.assertEqual(review['streak'], 1)

    def test_registration(self):
        response = self.client.post(reverse("api:auth:user-create"), data={
            'username': "createme",
            'password': "password",
            'api_key': constants.API_KEY,
            'email': 'asdf@email.com'
        })
        assert(response.status_code == 201)

    @responses.activate
    def test_when_user_resets_account_to_a_given_level_their_current_level_is_also_set(self):
        # Given
        mock_user_info_response(self.user.profile.api_key)
        self.client.force_login(self.user)
        assert(self.user.profile.level == 5)

        # When
        response = self.client.post(reverse("api:user-reset"), data={'level': 1})
        assert("Your account has been reset" in response.data['message'])

        # Then
        self.user.profile.refresh_from_db()
        assert(self.user.profile.level == 17)

    def test_review_correct_submissions_return_full_modified_review_object(self):
        self.client.force_login(self.user)
        previous_streak = self.review.streak
        previous_correct = self.review.correct

        response = self.client.post(reverse("api:review-correct", args=(self.review.id,)))
        self.assertEqual(response.data['id'], self.review.id)
        self.assertEqual(response.data['streak'], previous_streak + 1)
        self.assertEqual(response.data['correct'], previous_correct + 1)

    def test_review_incorrect_submissions_return_full_modified_review_object(self):
        self.client.force_login(self.user)

        # We have to bump this to two to be able to see the drop in streak.
        self.review.streak = 2
        self.review.save()
        self.review.refresh_from_db()

        previous_streak = self.review.streak
        previous_incorrect = self.review.incorrect

        response = self.client.post(reverse("api:review-incorrect", args=(self.review.id,)))
        self.assertEqual(response.data['id'], self.review.id)
        self.assertEqual(response.data['streak'], previous_streak - 1)
        self.assertEqual(response.data['incorrect'], previous_incorrect + 1)

