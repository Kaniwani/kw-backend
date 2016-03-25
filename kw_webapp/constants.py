import re

from collections import OrderedDict
from datetime import timedelta

SRS_TIMES = {
    0: 4,  # Apprentice
    1: 4,  # Apprentice
    2: 8,  # Apprentice (8 hours)
    3: 24,  # Guru (1 day)
    4: 72,  # Guru (3 days)
    5: 168,  # Guru (7 days)
    6: 336,  # Master  (14 days)
    7: 720,  # Master (30 days)
    8: 2160,  # Enlightened (90 days)
    9: 4320,  # Burned (180 days)
}

# The level arrangement I believe to be exposed by WK API.

KANIWANI_SRS_LEVELS = OrderedDict()
KANIWANI_SRS_LEVELS["apprentice"] = [0, 1, 2]
KANIWANI_SRS_LEVELS["guru"] = [3, 4, 5]
KANIWANI_SRS_LEVELS["master"] = [6, 7]
KANIWANI_SRS_LEVELS["enlightened"] = [8]
KANIWANI_SRS_LEVELS["burned"] = [9]

REVIEW_ROUNDING_TIME = timedelta(minutes=15)

WANIKANI_SRS_LEVELS = {
    "apprentice": [0, 1, 2, 3, 4],
    "guru": [5, 6],
    "master": [7],
    "enlightened": [8],
    "burned": [9]
}

LEVEL_MIN = 1
LEVEL_MAX = 60
API_KEY = "0158f285fa5e1254b84355ce92ccfa99"

TWITTER_USERNAME_REGEX = re.compile("[a-zA-Z0-9_]+")
HTTP_S_REGEX = re.compile("https?://")
