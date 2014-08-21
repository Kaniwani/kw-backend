from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test import Client

# Create your tests here.
from kw_webapp.models import Profile, Vocabulary, Reading, UserSpecific

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

def create_vocab(meaning):
    v = Vocabulary.objects.create(meaning=meaning)
    return v


def create_reading(vocab, reading, character, level):
    r = Reading.objects.create(vocabulary=vocab,
                               kana=reading, level=level, character=character)
    return r

def create_full_user_specific(meaning):
    v = create_vocab(meaning)
    r = create_reading(v, "cat", "cat", 1)
    u = create_user("Tadgh")
    us = create_userspecific(v, u)
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


class TestViews(TestCase):
    def setUp(self):
        self.c = Client()

    def test_review_requires_login(self):
        pass

    def test_recording_answer_works_on_correct_answer(self):
        us = create_full_user_specific("cat")
        self.c.post('/kw/record_answer/', {'user_correct': "true", 'user_specific_id': us.id})
        us = UserSpecific.objects.get(pk=us.id)
        print(us)
        recorded_properly = us.correct == 1 and us.streak == 1 and us.needs_review is False
        self.assertTrue(recorded_properly)

    def test_wrong_answer_records_failure(self):
        us = create_full_user_specific("dog")
        self.c.post('/kw/record_answer/', {'user_correct': "false", 'user_specific_id': us.id})
        us = UserSpecific.objects.get(pk=us.id)
        recorded_properly = (us.incorrect == 1 and us.streak == 0 and us.needs_review is True)
        self.assertTrue(recorded_properly)

    def test_nonexistent_user_specifc_id_raises_error_in_record_answer(self):
        response = self.c.post('/kw/record_answer/', {'user_correct': False, 'user_specific_id': 100})
        self.assertEquals(response.status_code, 404)

    def test_only_users_reviews_show_up(self):
        u1 = create_user("user1")
        u2 = create_user("user2")
        r1 = create_review_for_user(u1, "cat")
        r2 = create_review_for_user(u2, "dog")
        u1.authenticate()
        u1.login()

