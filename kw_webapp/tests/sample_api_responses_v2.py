single_vocab_v2 = {
      "id": 1,
      "object": "vocabulary",
      "url": "https://api.wanikani.com/v2/subjects/2468",
      "data_updated_at": "2018-12-12T23:10:32.253867Z",
      "data": {
        "created_at": "2012-02-28T08:10:16.000000Z",
        "level": 1,
        "slug": "一つ",
        "hidden_at": None,
        "document_url": "https://www.wanikani.com/vocabulary/%E4%B8%80%E3%81%A4",
        "characters": "current_character",
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
          }
        ],
        "auxiliary_meanings": [
          {
            "type": "whitelist",
            "meaning": "1 Thing"
          }
        ],
        "readings": [
          {
            "primary": True,
            "reading": "current_kana",
            "accepted_answer": True
          },
          {
            "primary": False,
            "reading": "swanky new kana",
            "accepted_answer": True
          }
        ],
        "parts_of_speech": [
          "verb", "definitely a verb"
        ],
        "component_subject_ids": [
          440
        ]
      }
    }

single_assignment = {
  "object": "collection",
  "url": "https://api.wanikani.com/v2/assignments?levels=10",
  "pages": {
    "per_page": 500,
    "next_url": None,
    "previous_url": None
  },
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
        "srs_stage_name": "Apprentice IV",
        "unlocked_at": "2018-07-27T17:21:59.578890Z",
        "started_at": "2018-07-30T01:57:17.619268Z",
        "passed_at": "2018-08-06T03:36:17.921419Z",
        "burned_at": None,
        "available_at": "2018-09-11T22:00:00.000000Z",
        "resurrected_at": None,
        "passed": None,
        "resurrected": None,
        "hidden": False
      }
    }
  ]
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
      "period_ends_at": None
    },
    "subscribed": True,
    "max_level_granted_by_subscription": 60,
    "current_vacation_started_at": None,
    "preferences": {
      "lessons_batch_size": 5,
      "lessons_autoplay_audio": True,
      "reviews_autoplay_audio": False,
      "lessons_presentation_order": "ascending_level_then_subject",
      "reviews_display_srs_indicator": True
    }
  }
}