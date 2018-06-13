from enum import Enum

import re

from collections import OrderedDict
from datetime import timedelta

# Check these values here: https://cdn.wanikani.com/assets/guide/srs-visualization-4580afac174836361bdc3d3758bd6c7f.png
SRS_TIMES = {
    # STREAK : HOURS_UNTIL_NEXT_REVIEW
    0: 4,  # Apprentice
    1: 4,  # Apprentice (4 hours)
    2: 8,  # Apprentice (8 hours)
    3: 24,  # Apprentice (1 day)
    4: 72,  # Apprentice -> Guru (3 days)
    5: 168,  # Guru (1 week)
    6: 336,  # Guru -> Master  (2 weeks)
    7: 720,  # Master -> Enlightened (1 month)
    8: 2880,  # Enlightened -> Burned (4 months)
}


class KwSrsLevel(Enum):
    UNTRAINED = "Untrained"
    APPRENTICE = "Apprentice"
    GURU = "Guru"
    MASTER = "Master"
    ENLIGHTENED = "Enlightened"
    BURNED = "Burned"

    @classmethod
    def choices(cls):
        return ((level.name, level.value) for level in KwSrsLevel)


class WkSrsLevel(Enum):
    APPRENTICE = "Apprentice"
    GURU = "Guru"
    MASTER = "Master"
    ENLIGHTENED = "Enlightened"
    BURNED = "Burned"

    @classmethod
    def choices(cls):
        return ((level.name, level.value) for level in WkSrsLevel)

# Internal SRS levels. Level 0 for us is lesson, whereas WK does not expose lessons at all.
KANIWANI_SRS_LEVELS = OrderedDict()
KANIWANI_SRS_LEVELS[KwSrsLevel.UNTRAINED.name] = [0]
KANIWANI_SRS_LEVELS[KwSrsLevel.APPRENTICE.name] = [1, 2, 3, 4]
KANIWANI_SRS_LEVELS[KwSrsLevel.GURU.name] = [5, 6]
KANIWANI_SRS_LEVELS[KwSrsLevel.MASTER.name] = [7]
KANIWANI_SRS_LEVELS[KwSrsLevel.ENLIGHTENED.name] = [8]
KANIWANI_SRS_LEVELS[KwSrsLevel.BURNED.name] = [9]

STREAK_TO_SRS_LEVEL_MAP_KW = OrderedDict()
STREAK_TO_SRS_LEVEL_MAP_KW[0] = KwSrsLevel.UNTRAINED
STREAK_TO_SRS_LEVEL_MAP_KW[1] = KwSrsLevel.APPRENTICE
STREAK_TO_SRS_LEVEL_MAP_KW[2] = KwSrsLevel.APPRENTICE
STREAK_TO_SRS_LEVEL_MAP_KW[3] = KwSrsLevel.APPRENTICE
STREAK_TO_SRS_LEVEL_MAP_KW[4] = KwSrsLevel.APPRENTICE
STREAK_TO_SRS_LEVEL_MAP_KW[5] = KwSrsLevel.GURU
STREAK_TO_SRS_LEVEL_MAP_KW[6] = KwSrsLevel.GURU
STREAK_TO_SRS_LEVEL_MAP_KW[7] = KwSrsLevel.MASTER
STREAK_TO_SRS_LEVEL_MAP_KW[8] = KwSrsLevel.ENLIGHTENED
STREAK_TO_SRS_LEVEL_MAP_KW[9] = KwSrsLevel.BURNED


# The level arrangement I believe to be exposed by WK API.
WANIKANI_SRS_LEVELS = OrderedDict()
WANIKANI_SRS_LEVELS[WkSrsLevel.APPRENTICE.name] = [0, 1, 2, 3, 4]
WANIKANI_SRS_LEVELS[WkSrsLevel.GURU.name] = [5, 6]
WANIKANI_SRS_LEVELS[WkSrsLevel.MASTER.name] = [7]
WANIKANI_SRS_LEVELS[WkSrsLevel.ENLIGHTENED.name] = [8]
WANIKANI_SRS_LEVELS[WkSrsLevel.BURNED.name] = [9]

REVIEW_ROUNDING_TIME = timedelta(minutes=15)

LEVEL_MIN = 1
LEVEL_MAX = 60
API_KEY = "0158f285fa5e1254b84355ce92ccfa99"

MIN_SVG_DRAW_SPEED = 1
MAX_SVG_DRAW_SPEED = 10
MAX_REVIEW_DETAIL_LEVEL = 2

MINIMUM_ATTEMPT_COUNT_FOR_CRITICALITY = 4
CRITICALITY_THRESHOLD = 0.75
# NOTE: we no longer display user's WK twitter/webpage bio info
# No plans to do so in the future
# Can safely remove these, associated tests, and model data for twitter/webpage
TWITTER_USERNAME_REGEX = re.compile("[a-zA-Z0-9_]+")
HTTP_S_REGEX = re.compile("https?://")


class Source(Enum):
    WANIKANI = "WaniKani"
    JISHO = "Jisho"

    @classmethod
    def choices(cls):
        return ((source.name, source.value) for source in Source)

SOURCES_TO_LOOKUP_URL_MAP = OrderedDict()
SOURCES_TO_LOOKUP_URL_MAP[Source.WANIKANI.name] = "https://www.wanikani.com/vocabulary/{}/"
SOURCES_TO_LOOKUP_URL_MAP[Source.JISHO.name] = "https://jisho.org/word/{}"