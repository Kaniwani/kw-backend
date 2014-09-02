from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import TestCase, RequestFactory
from django.test import Client
import kw_webapp.views

# Create your tests here.
from kw_webapp.models import Profile, Vocabulary, Reading, UserSpecific
from kw_webapp.tasks import all_srs, past_time, get_vocab_by_meaning, associate_vocab_to_user, \
    build_API_sync_string_for_user


def create_user(username):
    u = User.objects.create(username=username)
    return u

def create_userspecific(vocabulary, user):
    u = UserSpecific.objects.create(vocabulary=vocabulary, user=user)
    return u

def create_profile(user, api_key, level):
    p = Profile.objects.create(user=user, api_key=api_key, level=level)
    return p

def create_review_for_user(user, meaning):
    v = create_vocab(meaning)
    r = create_reading(v, "cat", "cat", 1)
    us = create_userspecific(v, user)
    return us

def create_vocab(meaning):
    v = Vocabulary.objects.create(meaning=meaning)
    return v


def create_reading(vocab, reading, character, level):
    r = Reading.objects.create(vocabulary=vocab,
                               kana=reading, level=level, character=character)
    return r

def create_full_user_specific(meaning, user):
    v = create_vocab(meaning)
    r = create_reading(v, "cat", "cat", 1)
    us = create_userspecific(v, user)
    return us

class TestModels(TestCase):
    def setUp(self):
        self.c = Client()


    def test_reading_clean_fails_with_invalid_levels_too_high(self):
        v = create_vocab("cat")
        r = create_reading(v,  "ねこ", "ねこ", 51)
        self.assertRaises(ValidationError, r.clean_fields)

    def test_reading_clean_fails_with_invalid_levels_too_low(self):
        v = create_vocab("cat")
        r = create_reading(v,  "ねこ", "ねこ", 0)
        self.assertRaises(ValidationError, r.clean_fields)

    def test_vocab_num_options_is_correct(self):
        v = create_vocab("cat")
        r = create_reading(v,  "ねこ", "ねこ", 2)
        r = create_reading(v,  "ねこな", "猫", 1)
        self.assertEqual(v.num_options(), 2)

    def test_available_readings_returns_only_readings_youve_unlocked(self):
        v = create_vocab("cat")
        r = create_reading(v,  "ねこ", "ねこ", 5)
        r = create_reading(v,  "ねこな", "猫", 1)
        self.assertTrue(len(v.available_readings(2)) == 1)

class TestCeleryTasks(TestCase):
    def setup(self):
        pass

    def test_srs_all_catches_all_reviews(self):
        u = create_user("Tadgh")
        review = create_full_user_specific("cat", u)
        review2 = create_full_user_specific("cat2", u)
        review.needs_review = False
        review2.needs_review = False
        review.last_studied = past_time(5)
        review2.last_studied = past_time(9)
        review2.streak = 1
        review.save()
        review2.save()
        all_srs()
        review = UserSpecific.objects.get(pk=review.id)
        review2 = UserSpecific.objects.get(pk=review2.id)
        self.assertTrue(review.needs_review and review2.needs_review)

    def test_get_vocab_by_meaning_gets_correct_vocab(self):
        vocab = create_vocab("cat")
        id = vocab.id
        found_vocab = get_vocab_by_meaning("cat")
        self.assertEqual(id, found_vocab.id)

    def test_get_vocab_by_meaning_raises_error_on_unknown_meaning(self):
        self.assertRaises(Vocabulary.DoesNotExist, get_vocab_by_meaning, "cat")

    def test_associate_vocab_to_user_successfully_creates_review(self):
        u = create_user("Tadgh")
        v = create_vocab("cat")
        r = create_reading(v, "cat", "neko", 1)
        review = associate_vocab_to_user(v, u)
        users_review = UserSpecific.objects.get(user=u, vocabulary=v)
        self.assertTrue(users_review.needs_review is True)

    def test_associating_an_existing_vocab_returns_nothing(self):
        u = create_user("Tadgh")
        v = create_vocab("cat")
        r = create_reading(v, "cat", "neko", 1)
        #First association creates the review
        review = associate_vocab_to_user(v, u)
        should_be_none = associate_vocab_to_user(v,u)
        self.assertTrue(should_be_none is None)

    def test_building_api_string_adds_correct_levels(self):
        u = create_user("Tadgh")
        p = Profile.objects.create(user=u)
        p.api_key = "test"
        p.level = 5
        p.unlocked_levels.create(level=5)
        p.unlocked_levels.create(level=3)
        p.unlocked_levels.create(level=1)
        p.save()

        api_call = build_API_sync_string_for_user(u)
        correct_string = "https://www.wanikani.com/api/user/test/vocabulary/5,3,"
        self.assertEqual(correct_string, api_call)



class TestViews(TestCase):
    def setUp(self):
        self.c = Client()
        self.the_user = create_user("user1")
        self.factory = RequestFactory()

    def test_review_requires_login(self):
        request = self.factory.get('/kw/review/')
        request.user = AnonymousUser()
        generic_view = kw_webapp.views.RecordAnswer.as_view()
        response = generic_view(request)
        self.assertEqual(response.status_code, 302)

    def test_recording_answer_works_on_correct_answer(self):
        us = create_full_user_specific("cat", self.the_user)

        #Generate and pass off the request
        request = self.factory.post('/kw/record_answer/', {'user_correct': "true", 'user_specific_id': us.id, 'wrong_before':'false'})
        request.user = AnonymousUser()
        generic_view = kw_webapp.views.RecordAnswer.as_view()
        generic_view(request)

        us = UserSpecific.objects.get(pk=us.id)
        recorded_properly = us.correct == 1 and us.streak == 1 and us.needs_review is False
        self.assertTrue(recorded_properly)

    def test_wrong_answer_records_failure(self):
        us = create_full_user_specific("dog", self.the_user)

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


