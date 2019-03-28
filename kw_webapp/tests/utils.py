from datetime import timedelta

import responses
from django.contrib.auth.models import User

from kw_webapp.constants import API_KEY
from kw_webapp.models import Vocabulary, Reading, UserSpecific, Profile
from kw_webapp.tasks import (
    build_API_sync_string_for_user_for_levels,
    build_API_sync_string_for_api_key_for_levels)

from requests.exceptions import ConnectionError
from kw_webapp.tests import sample_api_responses, sample_api_responses_v2


def create_user(username):
    u = User.objects.create(username=username)
    u.set_password(username)
    u.save()
    return u


def create_review(vocabulary, user):
    u = UserSpecific.objects.create(vocabulary=vocabulary, user=user)
    u.streak = 1
    u.save()
    return u


def create_lesson(vocabulary, user):
    u = UserSpecific.objects.create(vocabulary=vocabulary, user=user)
    u.streak = 0
    u.save()
    return u

def build_v1_user_information_api_string(api_key):
    return "https://www.wanikani.com/api/user/{}/user-information".format(api_key)

@responses.activate
def create_profile(user, api_key, level):
    try:
        p = Profile.objects.create(user=user, api_key=api_key, level=level)
    except ConnectionError as e:
        print("Ignore this failed connection....due to uninitialized mocks")
    p = Profile.objects.get(user=user)
    p.unlocked_levels.create(level=level)
    return p

def create_vocab(meaning):
    v = Vocabulary.objects.create(meaning=meaning)
    return v


def create_reading(vocab, reading, character, level):
    r = Reading.objects.create(
        vocabulary=vocab, kana=reading, level=level, character=character
    )
    return r


def create_review_for_specific_time(user, meaning, time_to_review):
    timed_review = create_review(create_vocab(meaning), user)
    timed_review.needs_review = False
    timed_review.streak = 1
    timed_review.last_studied = time_to_review + timedelta(hours=-6)
    timed_review.next_review_date = time_to_review
    timed_review.save()
    return timed_review


def build_test_api_string_for_merging():
    api_call = "https://www.wanikani.com/api/user/{}/vocabulary/TEST".format(API_KEY)
    return api_call

def mock_for_registration(api_key, wk_level):
    mock_vocab_list_response_with_single_vocabulary(api_key, wk_level)
    mock_user_info_response(api_key)

def mock_empty_vocabulary_response(api_key, level):
    responses.add(
        responses.GET,
        build_API_sync_string_for_api_key_for_levels(api_key, level),
        json=sample_api_responses.no_vocab_response,
        status=200,
        content_type="application/json",
    )

def mock_vocab_list_response_with_single_vocabulary(api_key, level):
    responses.add(
        responses.GET,
        build_API_sync_string_for_api_key_for_levels(api_key, level),
        json=sample_api_responses.single_vocab_response,
        status=200,
        content_type="application/json",
    )

def mock_vocab_list_response_with_single_vocabulary(user):
    responses.add(
        responses.GET,
        build_API_sync_string_for_user_for_levels(user, user.profile.level),
        json=sample_api_responses.single_vocab_response,
        status=200,
        content_type="application/json",
    )

def mock_user_info_response_at_level(api_key, level):
    responses.add(
        responses.GET,
        build_v1_user_information_api_string(api_key),
        json=sample_api_responses.user_information_response_at_level(level),
        status=200,
        content_type="application/json",
    )

def mock_user_info_response_with_higher_level(api_key):
    responses.add(
        responses.GET,
        build_v1_user_information_api_string(api_key),
        json=sample_api_responses.user_information_response_with_higher_level,
        status=200,
        content_type="application/json",
    )


def mock_user_info_response(api_key):
    responses.add(
        responses.GET,
        build_v1_user_information_api_string(api_key),
        json=sample_api_responses.user_information_response,
        status=200,
        content_type="application/json",
    )

def mock_study_materials():
    responses.add(
        responses.GET,
        build_study_materials_url(),
        json=sample_api_responses_v2.single_study_material,
        status=200,
        content_type="application/json"
    )

def _mock_wk_response(url, json):
    responses.add(
        responses.GET,
        url,
        json=json,
        status=200,
        content_type="application/json"
    )
def mock_assignments_with_one_assignment():
    _mock_wk_response(build_assignments_url(), sample_api_responses_v2.single_assignment)

def mock_user_response_v2():
    responses.add(
        responses.GET,
        "https://api.wanikani.com/v2/user",
        json=sample_api_responses_v2.user_profile,
        status=200,
        content_type="application/json"
    )

def mock_subjects_v2():
    responses.add(
        responses.GET,
        "https://api.wanikani.com/v2/subjects",
        json=sample_api_responses_v2.subjects_v2,
        status=200,
        content_type="application/json",
        headers={"Etag": "sampleEtag"}
    )

def build_assignments_url():
    return "https://api.wanikani.com/v2/assignments"

def build_study_materials_url():
    return "https://api.wanikani.com/v2/study_materials"

def mock_invalid_api_user_info_response(api_key):
    responses.add(
        responses.GET,
        build_v1_user_information_api_string(api_key),
        json={"Nothing": "Nothing"},
        status=401,
        content_type="application/json",
    )

def mock_anything_to_wanikani_to_401():
    #TODO write this function.
    pass

def mock_vocab_list_response_with_single_vocabulary_with_four_synonyms(user):
    responses.add(
        responses.GET,
        build_API_sync_string_for_user_for_levels(user, [user.profile.level]),
        json=sample_api_responses.single_vocab_response_with_4_meaning_synonyms,
        status=200,
        content_type="application/json",
    )

def mock_vocab_list_response_with_single_vocabulary(api_key, level):
    responses.add(
        responses.GET,
        build_API_sync_string_for_api_key_for_levels(api_key, level),
        json=sample_api_responses.single_vocab_response_with_changed_meaning,
        status=200,
        content_type="application/json",
    )

def mock_vocab_list_response_with_single_vocabulary_with_changed_meaning(user):
    responses.add(
        responses.GET,
        build_API_sync_string_for_user_for_levels(user, [user.profile.level]),
        json=sample_api_responses.single_vocab_response_with_changed_meaning,
        status=200,
        content_type="application/json",
    )


def setupTestFixture(self):
    # Setup an admin user.
    self.admin = create_user("admin")
    create_profile(self.admin, "any_key", 5)
    self.admin.is_staff = True
    self.admin.save()

    # Setup a non-admin user.
    self.user = create_user("Tadgh")
    create_profile(self.user, "any_key", 5)

    # Setup some basic vocabulary / reading / review information.
    self.vocabulary = create_vocab("radioactive bat")
    self.vocabulary.wk_subject_id = 1
    self.vocabulary.save()
    self.reading = create_reading(self.vocabulary, "ねこ", "猫", 5)
    self.reading.furigana_sentence_ja = {
        "preamble": ["その"],
        "focus": [["議員", "0:ぎ;1:いん"]],
        "postamble": [
            "は、",
            ["公私", "0:こう;1:し"],
            "のけじめをつけることを",
            ["学ぶ", "0:まな"],
            ["必要", "0:ひつ;1:よう"],
            "があります",
        ],
    }
    self.reading.save()
    self.review = create_review(self.vocabulary, self.user)
