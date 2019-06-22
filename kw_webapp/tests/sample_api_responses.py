single_vocab_response = {
    "user_information": {
        "username": "Tadgh11",
        "gravatar": "a9453be85d2e722fd7e3b3424a38be30",
        "level": 16,
        "title": "Turtles",
        "about": "",
        "website": "http://www.kaniwani.com",
        "twitter": "@Tadgh11",
        "topics_count": 1,
        "posts_count": 81,
        "creation_date": 1373371374,
        "vacation_date": None,
    },
    "requested_information": [
        {
            "character": "猫",
            "kana": "ねこ",
            "meaning": "radioactive bat",
            "level": 16,
            "user_specific": {
                "srs": "apprentice",
                "srs_numeric": 3,
                "unlocked_date": 1448398437,
                "available_date": 1448586000,
                "burned": False,
                "burned_date": 0,
                "meaning_correct": 0,
                "meaning_incorrect": 0,
                "meaning_max_streak": 0,
                "meaning_current_streak": 0,
                "reading_correct": 0,
                "reading_incorrect": 0,
                "reading_max_streak": 0,
                "reading_current_streak": 0,
                "meaning_note": None,
                "user_synonyms": [],
                "reading_note": None,
            },
        }
    ],
}

no_vocab_response = {
    "user_information": {
        "username": "Tadgh11",
        "gravatar": "a9453be85d2e722fd7e3b3424a38be30",
        "level": 16,
        "title": "Turtles",
        "about": "",
        "website": "http://www.kaniwani.com",
        "twitter": "@Tadgh11",
        "topics_count": 1,
        "posts_count": 81,
        "creation_date": 1373371374,
        "vacation_date": None,
    },
    "requested_information": [
        {
            "character": "猫",
            "kana": "ねこ",
            "meaning": "radioactive bat",
            "level": 16,
            "user_specific": None,
        }
    ],
}

single_vocab_existing_meaning_and_should_now_merge = {
    "user_information": {
        "username": "Tadgh11",
        "gravatar": "a9453be85d2e722fd7e3b3424a38be30",
        "level": 16,
        "title": "Turtles",
        "about": "",
        "website": "http://www.kaniwani.com",
        "twitter": "@Tadgh11",
        "topics_count": 1,
        "posts_count": 81,
        "creation_date": 1373371374,
        "vacation_date": None,
    },
    "requested_information": [
        {
            "character": "犬",
            "kana": "ねこ",
            "meaning": "dog, woofer, pupper",
            "level": 5,
            "user_specific": {
                "srs": "apprentice",
                "srs_numeric": 3,
                "unlocked_date": 1448398437,
                "available_date": 1448586000,
                "burned": False,
                "burned_date": 0,
                "meaning_correct": 0,
                "meaning_incorrect": 0,
                "meaning_max_streak": 0,
                "meaning_current_streak": 0,
                "reading_correct": 0,
                "reading_incorrect": 0,
                "reading_max_streak": 0,
                "reading_current_streak": 0,
                "meaning_note": None,
                "user_synonyms": [],
                "reading_note": None,
            },
        }
    ],
}

single_vocab_new_meaning_and_should_now_merge = {
    "user_information": {
        "username": "Tadgh11",
        "gravatar": "a9453be85d2e722fd7e3b3424a38be30",
        "level": 16,
        "title": "Turtles",
        "about": "",
        "website": "http://www.kaniwani.com",
        "twitter": "@Tadgh11",
        "topics_count": 1,
        "posts_count": 81,
        "creation_date": 1373371374,
        "vacation_date": None,
    },
    "requested_information": [
        {
            "character": "猫",
            "kana": "ねこ",
            "meaning": "DOGGO",  # was previously radioactive bat. Has now changed, and should be aglomerated with original DOGGO
            "level": 16,
            "user_specific": {
                "srs": "apprentice",
                "srs_numeric": 3,
                "unlocked_date": 1448398437,
                "available_date": 1448586000,
                "burned": False,
                "burned_date": 0,
                "meaning_correct": 0,
                "meaning_incorrect": 0,
                "meaning_max_streak": 0,
                "meaning_current_streak": 0,
                "reading_correct": 0,
                "reading_incorrect": 0,
                "reading_max_streak": 0,
                "reading_current_streak": 0,
                "meaning_note": None,
                "user_synonyms": [],
                "reading_note": None,
            },
        }
    ],
}

added_meaning_to_conglomerate_vocab_sample_response = {
    "user_information": {
        "username": "Tadgh11",
        "gravatar": "a9453be85d2e722fd7e3b3424a38be30",
        "level": 16,
        "title": "Turtles",
        "about": "",
        "website": "http://www.kaniwani.com",
        "twitter": "@Tadgh11",
        "topics_count": 1,
        "posts_count": 81,
        "creation_date": 1373371374,
        "vacation_date": None,
    },
    "requested_information": [
        {
            "character": "工作",
            "kana": "ねこ",
            "meaning": "construction, handicraft",
            "level": 2,
            "user_specific": {
                "srs": "burned",
                "srs_numeric": 9,
                "unlocked_date": 1448398437,
                "available_date": 1448586000,
                "burned": True,
                "burned_date": 0,
                "meaning_correct": 9,
                "meaning_incorrect": 0,
                "meaning_max_streak": 9,
                "meaning_current_streak": 0,
                "reading_correct": 0,
                "reading_incorrect": 0,
                "reading_max_streak": 0,
                "reading_current_streak": 0,
                "meaning_note": None,
                "user_synonyms": [],
                "reading_note": None,
            },
        }
    ],
}

user_information_response_with_higher_level = {
    "user_information": {
        "username": "Tadgh11",
        "gravatar": "a9453be85d2e722fd7e3b3424a38be30",
        "level": 17,
        "title": "Turtles",
        "about": "",
        "website": "http://www.kaniwani.com",
        "twitter": "@Tadgh11",
        "topics_count": 1,
        "posts_count": 81,
        "creation_date": 1373371374,
        "vacation_date": None,
    }
}


def user_information_response_at_level(level):
    return {
        "user_information": {
            "username": "Tadgh11",
            "gravatar": "a9453be85d2e722fd7e3b3424a38be30",
            "level": level,
            "title": "Turtles",
            "about": "",
            "website": "http://www.kaniwani.com",
            "twitter": "@Tadgh11",
            "topics_count": 1,
            "posts_count": 81,
            "creation_date": 1373371374,
            "vacation_date": None,
        }
    }


user_information_response_at_level_1 = {
    "user_information": {
        "username": "Tadgh11",
        "gravatar": "a9453be85d2e722fd7e3b3424a38be30",
        "level": 1,
        "title": "Turtles",
        "about": "",
        "website": "http://www.kaniwani.com",
        "twitter": "@Tadgh11",
        "topics_count": 1,
        "posts_count": 81,
        "creation_date": 1373371374,
        "vacation_date": None,
    }
}
user_information_response = {
    "user_information": {
        "username": "Tadgh11",
        "gravatar": "a9453be85d2e722fd7e3b3424a38be30",
        "level": 5,
        "title": "Turtles",
        "about": "",
        "website": "http://www.kaniwani.com",
        "twitter": "@Tadgh11",
        "topics_count": 1,
        "posts_count": 81,
        "creation_date": 1373371374,
        "vacation_date": None,
    }
}

single_vocab_requested_information = {
    "character": "bleh",
    "kana": "bleh",
    "meaning": "two",
    "level": 1,
    "user_specific": {
        "srs": "burned",
        "srs_numeric": 9,
        "unlocked_date": 1382674360,
        "available_date": 1398364200,
        "burned": True,
        "burned_date": 1398364287,
        "meaning_correct": 8,
        "meaning_incorrect": 0,
        "meaning_max_streak": 8,
        "meaning_current_streak": 8,
        "reading_correct": 8,
        "reading_incorrect": 0,
        "reading_max_streak": 8,
        "reading_current_streak": 8,
        "meaning_note": None,
        "user_synonyms": None,
        "reading_note": None,
    },
}


single_vocab_response_with_4_meaning_synonyms = {
    "user_information": {
        "username": "Tadgh11",
        "gravatar": "a9453be85d2e722fd7e3b3424a38be30",
        "level": 16,
        "title": "Turtles",
        "about": "",
        "website": "http://www.kaniwani.com",
        "twitter": "@Tadgh11",
        "topics_count": 1,
        "posts_count": 81,
        "creation_date": 1373371374,
        "vacation_date": None,
    },
    "requested_information": [
        {
            "character": "猫",
            "kana": "ねこ",
            "meaning": "radioactive bat",
            "level": 16,
            "user_specific": {
                "srs": "apprentice",
                "srs_numeric": 3,
                "unlocked_date": 1448398437,
                "available_date": 1448586000,
                "burned": False,
                "burned_date": 0,
                "meaning_correct": 0,
                "meaning_incorrect": 0,
                "meaning_max_streak": 0,
                "meaning_current_streak": 0,
                "reading_correct": 0,
                "reading_incorrect": 0,
                "reading_max_streak": 0,
                "reading_current_streak": 0,
                "meaning_note": None,
                "user_synonyms": [
                    "synonym_1",
                    "synonym_2",
                    "synonym_3",
                    "synonym_4",
                ],
                "reading_note": None,
            },
        }
    ],
}

single_vocab_response_with_changed_meaning = {
    "user_information": {
        "username": "Tadgh11",
        "gravatar": "a9453be85d2e722fd7e3b3424a38be30",
        "level": 16,
        "title": "Turtles",
        "about": "",
        "website": "http://www.kaniwani.com",
        "twitter": "@Tadgh11",
        "topics_count": 1,
        "posts_count": 81,
        "creation_date": 1373371374,
        "vacation_date": None,
    },
    "requested_information": [
        {
            "character": "猫",
            "kana": "ねこ",
            "meaning": "radioactive bat, added meaning, new meaning.",
            "level": 16,
            "user_specific": {
                "srs": "apprentice",
                "srs_numeric": 3,
                "unlocked_date": 1448398437,
                "available_date": 1448586000,
                "burned": False,
                "burned_date": 0,
                "meaning_correct": 0,
                "meaning_incorrect": 0,
                "meaning_max_streak": 0,
                "meaning_current_streak": 0,
                "reading_correct": 0,
                "reading_incorrect": 0,
                "reading_max_streak": 0,
                "reading_current_streak": 0,
                "meaning_note": None,
                "user_synonyms": [
                    "synonym_1",
                    "synonym_2",
                    "synonym_3",
                    "synonym_4",
                ],
                "reading_note": None,
            },
        }
    ],
}
