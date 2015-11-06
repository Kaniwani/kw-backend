from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import TestCase, RequestFactory
from django.test import Client
import kw_webapp.views

# Create your tests here.
from kw_webapp.models import Profile, Vocabulary, Reading, UserSpecific, Synonym
from kw_webapp.tasks import all_srs, past_time, get_vocab_by_meaning, associate_vocab_to_user, \
    build_API_sync_string_for_user, create_new_vocabulary

## Helper Methods
def create_user(username):
    u = User.objects.create(username=username)
    return u

def create_userspecific(vocabulary, user):
    u = UserSpecific.objects.create(vocabulary=vocabulary, user=user)
    u.save()
    return u

def create_profile(user, api_key, level):
    p = Profile.objects.create(user=user, api_key=api_key, level=level)
    return p

def create_vocab(meaning):
    v = Vocabulary.objects.create(meaning=meaning)
    return v

def create_reading(vocab, reading, character, level):
    r = Reading.objects.create(vocabulary=vocab,
                               kana=reading, level=level, character=character)
    return r

class TestModels(TestCase):
    def setUp(self):
        self.c = Client()
        self.user = create_user("Tadgh")
        self.vocabulary = create_vocab("cat")
        self.review = create_userspecific(self.vocabulary, self.user)
        self.review.synonym_set.get_or_create(text="minou")

    def test_adding_synonym_works(self):
        self.review.synonym_set.get_or_create(text="une petite chatte")
        self.assertEqual(2, len(self.review.synonym_set.all()))

    def test_removing_synonym_by_lookup_works(self):
        remove_text = "minou"
        self.review.remove_synonym(remove_text)
        self.assertNotIn(remove_text, self.review.synonyms_list())

    def test_removing_nonexistent_synonym_fails(self):
        remove_text = "un chien"
        self.assertRaises(Synonym.DoesNotExist, self.review.remove_synonym, remove_text)

    def test_removing_synonym_by_object_works(self):
        synonym, created = self.review.synonym_set.get_or_create(text="minou")
        self.review.synonym_set.remove(synonym)

    def test_reading_clean_fails_with_invalid_levels_too_high(self):
        v = create_vocab("cat")
        r = create_reading(v,  "ねこ", "ねこ", 51)

        self.assertRaises(ValidationError, r.clean_fields)

    def test_reading_clean_fails_with_invalid_levels_too_low(self):
        v = create_vocab("cat")
        r = create_reading(v,  "ねこ", "ねこ", 0)

        self.assertRaises(ValidationError, r.clean_fields)

    def test_vocab_number_readings_is_correct(self):
        r = create_reading(self.vocabulary,  "ねこ", "ねこ", 2)
        r = create_reading(self.vocabulary,  "ねこな", "猫", 1)
        self.assertEqual(self.vocabulary.reading_count(), 2)

    def test_available_readings_returns_only_readings_youve_unlocked(self):
        v = create_vocab("cat")
        r = create_reading(v,  "ねこ", "ねこ", 5)
        r = create_reading(v,  "ねこな", "猫", 1)

        self.assertTrue(len(v.available_readings(2)) == 1)

    def test_synonym_adding(self):

        review = create_userspecific(self.vocabulary, self.user)

        review.synonym_set.get_or_create(text="kitty")

        self.assertIn("kitty", [synonym.text for synonym in review.synonym_set.all()])

class TestCeleryTasks(TestCase):
    def setUp(self):
        self.user = create_user("Tadgh")
        self.vocabulary = create_vocab("cat")
        self.review = create_userspecific(self.vocabulary, self.user)

    def test_userspecifics_needing_review_are_flagged(self):
        self.review.needs_review = False
        self.review.last_studied = past_time(5)
        self.review.save()
        all_srs()
        review = UserSpecific.objects.get(pk=self.review.id)
        self.assertTrue(review.needs_review)

    def test_get_vocab_by_meaning_gets_correct_vocab(self):
        vocab_id = self.vocabulary.id
        found_vocab = get_vocab_by_meaning("cat")
        self.assertEqual(vocab_id, found_vocab.id)

    def test_get_vocab_by_meaning_raises_error_on_unknown_meaning(self):
        self.assertRaises(Vocabulary.DoesNotExist, get_vocab_by_meaning, "dog!")

    def test_associate_vocab_to_user_successfully_creates_review(self):
        review = associate_vocab_to_user(self.vocabulary, self.user)
        self.assertTrue(review.needs_review is True)

    def test_building_api_string_adds_correct_levels(self):
        p = create_profile(self.user, "test", 5)
        p.unlocked_levels.create(level=5)
        p.unlocked_levels.create(level=3)
        p.unlocked_levels.create(level=1)
        p.save()

        api_call = build_API_sync_string_for_user(self.user)
        correct_string = "https://www.wanikani.com/api/user/test/vocabulary/5,3,"

        self.assertEqual(correct_string, api_call)

    def test_create_new_vocab_based_on_json_works(self):
        vocab_json = {"character": "bleh", "kana": "bleh", "meaning": "two", "level": 1, "user_specific": {"srs": "burned","srs_numeric": 9,"unlocked_date": 1382674360,"available_date": 1398364200,"burned": True,"burned_date": 1398364287,"meaning_correct": 8,"meaning_incorrect": 0,"meaning_max_streak": 8,"meaning_current_streak": 8,"reading_correct": 8,"reading_incorrect": 0,"reading_max_streak": 8,"reading_current_streak": 8,"meaning_note": None,"user_synonyms": None,"reading_note": None}}
        vocab = create_new_vocabulary(vocab_json)
        self.assertIsInstance(vocab, Vocabulary)



class TestViews(TestCase):
    def setUp(self):
        self.c = Client()
        self.user = create_user("user1")
        self.factory = RequestFactory()
        self.cat_vocab = create_vocab("cat")

    def test_review_requires_login(self):
        request = self.factory.get('/kw/review/')
        request.user = AnonymousUser()
        generic_view = kw_webapp.views.RecordAnswer.as_view()
        response = generic_view(request)
        self.assertEqual(response.status_code, 302)

    def test_recording_answer_works_on_correct_answer(self):
        us = create_userspecific(self.cat_vocab, self.user)

        #Generate and pass off the request
        request = self.factory.post('/kw/record_answer/', {'user_correct': "true", 'user_specific_id': us.id, 'wrong_before':'false'})
        request.user = AnonymousUser()
        generic_view = kw_webapp.views.RecordAnswer.as_view()
        generic_view(request)

        us = UserSpecific.objects.get(pk=us.id)
        recorded_properly = us.correct == 1 and us.streak == 1 and us.needs_review is False
        self.assertTrue(recorded_properly)

    def test_wrong_answer_records_failure(self):
        vocab = create_vocab("dog")
        us = create_userspecific(vocab, self.user)

        #Generate and pass off the request
        request = self.factory.post('/kw/record_answer/', {'user_correct': "false", 'user_specific_id': us.id,  'wrong_before':'false'})
        request.user = AnonymousUser()
        generic_view =kw_webapp.views.RecordAnswer.as_view()
        response = generic_view(request)

        #grab it again and ensure it's correct.
        us = UserSpecific.objects.get(pk=us.id)
        recorded_properly = (us.incorrect == 1 and us.streak == 0 and us.needs_review is True)
        self.assertTrue(recorded_properly)

    def test_nonexistent_user_specific_id_raises_error_in_record_answer(self):

        #Generate and pass off the request
        request = self.factory.post('/kw/record_answer/', {'user_correct': "true", 'user_specific_id': 150, 'wrong_before':'false'})
        request.user = AnonymousUser()
        generic_view = kw_webapp.views.RecordAnswer.as_view()

        self.assertRaises(Http404, generic_view, request)

   # def test_vocab_page_contains_only_unlocked_vocab(self):
   #     u = create_user("Tadgh")
   #     v1 = create_vocab("cat")
   #     r1 = create_reading(v1, "猫", "ねこ", 5)
   #     v2 = create_vocab("dog")
   #     r2 = create_reading(v2, "犬", "いぬ", 5)
   #     review = create_userspecific(v1, u)
   #     request = self.factory.get('/kw/vocabulary')
   #     request.user = u
   #     returned_response = kw_webapp.views.UnlockedVocab.as_view()(request).render().content
   #     self.assertIn("cat", str(returned_response))

