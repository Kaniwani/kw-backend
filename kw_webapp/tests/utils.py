from django.contrib.auth.models import User
from kw_webapp.models import Vocabulary, Reading, UserSpecific, Profile


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
