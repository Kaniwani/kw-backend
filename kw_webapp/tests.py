from django.core.exceptions import ValidationError
from django.test import TestCase
# Create your tests here.
from kw_webapp.models import Profile, Vocabulary, Reading


def create_vocab(meaning):
    v = Vocabulary.objects.create(meaning=meaning)
    return v


def create_reading(vocab, reading, character, level ):
    r = Reading.objects.create(vocabulary=vocab, kana=reading, level=level, character=character)
    return r


class TestModels(TestCase):
    def setUp(self):
        pass

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
        pass

    def test_review_requires_login(self):
        pass

