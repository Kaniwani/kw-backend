single_vocab_v2 = {
    "id": 2468,
    "object": "vocabulary",
    "url": "https://api.wanikani.com/v2/subjects/2468",
    "data_updated_at": "2019-02-21T00:13:06.623548Z",
    "data": {
        "created_at": "2012-02-28T08:10:16.000000Z",
        "level": 1,
        "slug": "一つ",
        "hidden_at": None,
        "document_url": "https://www.wanikani.com/vocabulary/%E4%B8%80%E3%81%A4",
        "characters": "一つ",
        "meanings": [
            {
                "meaning": "Doesnt matter",
                "primary": True,
                "accepted_answer": True,
            },
            {
                "meaning": "secondary doesnt matter",
                "primary": False,
                "accepted_answer": True,
            },
        ],
        "auxiliary_meanings": [{"type": "whitelist", "meaning": "1 Thing"}],
        "readings": [
            {
                "primary": True,
                "reading": "current_kana",
                "accepted_answer": True,
            },
            {
                "primary": False,
                "reading": "swanky new kana",
                "accepted_answer": True,
            },
        ],
        "parts_of_speech": ["verb", "definitely a verb"],
        "component_subject_ids": [440],
        "meaning_mnemonic": 'This word follows the "number of things" pattern where there\'s a kanji for a number plus つ on the end. Whenever you see this, you know the word means "____ things." Knowing that, as long as you know the kanji (which you do) you can figure out what number of things it is. For this one, it\'s the kanji for <kanji>one</kanji> plus つ. So, this one is <vocabulary>one thing</vocabulary>.',
        "reading_mnemonic": "Since all of the \"number of things\" words all follow the same pattern (number plus つ), you really just have to remember the part before the つ (and then remember that the つ is in all of these). All of the readings are the kun'yomi reading, which means we'll have to use a mnemonic to remember them (you know the on'yomi reading of the kanji portion).\r\n\r\nSo, you have <vocabulary>one thing</vocabulary>. What one thing do you have? You have one of He-Man's Toes, aka a single <reading>He-Toe</reading> (ひと). So what's the thing you have only one of? You have one He-Toe. Imagine He-Man walking around with one missing toe, trying to find you so he can get it back. At least you'll be able to run faster than him now.",
        "context_sentences": [
            {"en": "Choose one answer.", "ja": "こたえを一つえらびます。"},
            {"en": "It's limited to one per customer.", "ja": "お一人さま一つかぎりです。"},
            {
                "en": "I met a one-eyed goblin yesterday.",
                "ja": "きのう、一つめこぞうにあった。",
            },
        ],
        "pronunciation_audios": [
            {
                "url": "https://cdn.wanikani.com/audios/3050-subject-2468.mp3?1547862363",
                "metadata": {
                    "gender": "male",
                    "source_id": 2714,
                    "pronunciation": "ひとつ",
                    "voice_actor_id": 2,
                    "voice_actor_name": "Kenichi",
                    "voice_description": "Tokyo accent",
                },
                "content_type": "audio/mpeg",
            },
            {
                "url": "https://cdn.wanikani.com/audios/3047-subject-2468.ogg?1547862363",
                "metadata": {
                    "gender": "male",
                    "source_id": 2714,
                    "pronunciation": "ひとつ",
                    "voice_actor_id": 2,
                    "voice_actor_name": "Kenichi",
                    "voice_description": "Tokyo accent",
                },
                "content_type": "audio/ogg",
            },
        ],
        "lesson_position": 45,
    },
}

subjects_v2 = {
    "object": "collection",
    "url": "https://api.wanikani.com/v2/subjects?types=vocabulary",
    "pages": {"per_page": 1000, "next_url": None, "previous_url": None},
    "total_count": 1,
    "data_updated_at": "2019-02-21T01:48:19.241116Z",
    "data": [
        {
            "id": 1,
            "object": "vocabulary",
            "url": "https://api.wanikani.com/v2/subjects/2467",
            "data_updated_at": "2019-02-21T00:13:06.456212Z",
            "data": {
                "created_at": "2012-02-28T08:04:47.000000Z",
                "level": 1,
                "slug": "一",
                "hidden_at": None,
                "document_url": "https://www.wanikani.com/vocabulary/%E4%B8%80",
                "characters": "一",
                "meanings": [
                    {
                        "meaning": "One",
                        "primary": True,
                        "accepted_answer": True,
                    }
                ],
                "auxiliary_meanings": [
                    {"type": "whitelist", "meaning": "1"},
                    {"type": "whitelist", "meaning": "uno"},
                ],
                "readings": [
                    {
                        "primary": True,
                        "reading": "いち",
                        "accepted_answer": True,
                    },
                    {
                        "primary": False,
                        "reading": "one - but in japanese",
                        "accepted_answer": True,
                    },
                ],
                "parts_of_speech": ["numeral"],
                "component_subject_ids": [440],
                "meaning_mnemonic": "As is the case with most vocab words that consist of a single kanji, this vocab word has the same meaning as the kanji it parallels, which is <vocabulary>one</vocabulary>.",
                "reading_mnemonic": "When a vocab word is all alone and has no okurigana (hiragana attached to kanji) connected to it, it usually uses the kun'yomi reading. Numbers are an exception, however. When a number is all alone, with no kanji or okurigana, it is going to be the on'yomi reading, which you learned with the kanji.  Just remember this exception for alone numbers and you'll be able to read future number-related vocab to come.",
                "context_sentences": [
                    {"en": "Let’s meet up once.", "ja": "一ど、あいましょう。"},
                    {
                        "en": "First place was an American.",
                        "ja": "一いはアメリカ人でした。",
                    },
                    {
                        "en": "I’m the weakest man in the world.",
                        "ja": "ぼくはせかいで一ばんよわい。",
                    },
                ],
                "pronunciation_audios": [
                    {
                        "url": "https://cdn.wanikani.com/audios/3020-subject-2467.mp3?1547862356",
                        "metadata": {
                            "gender": "male",
                            "source_id": 2711,
                            "pronunciation": "いち",
                            "voice_actor_id": 2,
                            "voice_actor_name": "Kenichi",
                            "voice_description": "Tokyo accent",
                        },
                        "content_type": "audio/mpeg",
                    },
                    {
                        "url": "https://cdn.wanikani.com/audios/3018-subject-2467.ogg?1547862356",
                        "metadata": {
                            "gender": "male",
                            "source_id": 2711,
                            "pronunciation": "いち",
                            "voice_actor_id": 2,
                            "voice_actor_name": "Kenichi",
                            "voice_description": "Tokyo accent",
                        },
                        "content_type": "audio/ogg",
                    },
                ],
                "lesson_position": 44,
            },
        }
    ],
}

no_assignments = {
    "object": "collection",
    "url": "https://api.wanikani.com/v2/assignments?levels=10",
    "pages": {"per_page": 500, "next_url": None, "previous_url": None},
    "total_count": 0,
    "data_updated_at": "2019-02-18T02:50:55.384575Z",
    "data": [],
}

single_assignment = {
    "object": "collection",
    "url": "https://api.wanikani.com/v2/assignments?levels=10",
    "pages": {"per_page": 500, "next_url": None, "previous_url": None},
    "total_count": 1,
    "data_updated_at": "2019-02-18T02:50:55.384575Z",
    "data": [
        {
            "id": 1318994,
            "object": "assignment",
            "url": "https://api.wanikani.com/v2/assignments/1318994",
            "data_updated_at": "2018-09-09T23:25:30.518490Z",
            "data": {
                "created_at": "2017-05-03T21:47:11.394197Z",
                "subject_id": 1,
                "subject_type": "vocabulary",
                "srs_stage": 4,
                "unlocked_at": "2018-07-27T17:21:59.578890Z",
                "started_at": "2018-07-30T01:57:17.619268Z",
                "passed_at": "2018-08-06T03:36:17.921419Z",
                "burned_at": None,
                "available_at": "2018-09-11T22:00:00.000000Z",
                "resurrected_at": None,
                "passed": None,
                "resurrected": None,
                "hidden": False,
            },
        }
    ],
}

user_profile = {
    "object": "user",
    "url": "https://api.wanikani.com/v2/user",
    "data_updated_at": "2019-02-18T02:48:36.476682Z",
    "data": {
        "id": "7a18daeb-4067-4e77-b0ea-230c7c347ea8",
        "username": "Tadgh11",
        "level": 12,
        "profile_url": "https://www.wanikani.com/users/Tadgh11",
        "started_at": "2013-07-09T12:02:54.952786Z",
        "subscription": {
            "active": True,
            "type": "lifetime",
            "max_level_granted": 60,
            "period_ends_at": None,
        },
        "subscribed": True,
        "max_level_granted_by_subscription": 60,
        "current_vacation_started_at": None,
        "preferences": {
            "lessons_batch_size": 5,
            "lessons_autoplay_audio": True,
            "reviews_autoplay_audio": False,
            "lessons_presentation_order": "ascending_level_then_subject",
            "reviews_display_srs_indicator": True,
        },
    },
}

single_study_material = {
    "object": "collection",
    "url": "https://api.wanikani.com/v2/study_materials",
    "pages": {"per_page": 500, "next_url": None, "previous_url": None},
    "total_count": 1,
    "data_updated_at": "2018-08-26T00:05:50.331703Z",
    "data": [
        {
            "id": 1539170,
            "object": "study_material",
            "url": "https://api.wanikani.com/v2/study_materials/1539170",
            "data_updated_at": "2017-06-01T19:01:36.573350Z",
            "data": {
                "created_at": "2017-02-01T15:55:42.058583Z",
                "subject_id": 1,
                "subject_type": "vocabulary",
                "meaning_note": "Sample meaning note",
                "reading_note": "Sample reading note",
                "meaning_synonyms": ["young girl", "young lady", "young miss"],
                "hidden": False,
            },
        }
    ],
}
