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


class SrsLevel(Enum):
    APPRENTICE = "Apprentice"
    GURU = "Guru"
    MASTER = "Master"
    ENLIGHTENED = "Enlightened"
    BURNED = "Burned"

    @classmethod
    def choices(cls):
        return ((level.name, level.value) for level in SrsLevel)

# The level arrangement I believe to be exposed by WK API.
KANIWANI_SRS_LEVELS = OrderedDict()
KANIWANI_SRS_LEVELS[SrsLevel.APPRENTICE.name] = [0, 1, 2, 3, 4]
KANIWANI_SRS_LEVELS[SrsLevel.GURU.name] = [5, 6]
KANIWANI_SRS_LEVELS[SrsLevel.MASTER.name] = [7]
KANIWANI_SRS_LEVELS[SrsLevel.ENLIGHTENED.name] = [8]
KANIWANI_SRS_LEVELS[SrsLevel.BURNED.name] = [9]

REVIEW_ROUNDING_TIME = timedelta(minutes=15)

LEVEL_MIN = 1
LEVEL_MAX = 60
API_KEY = "0158f285fa5e1254b84355ce92ccfa99"

MINIMUM_ATTEMPT_COUNT_FOR_CRITICALITY = 3
CRITICALITY_THRESHOLD = 0.75
# NOTE: we no longer display user's WK twitter/webpage bio info
# No plans to do so in the future
# Can safely remove these, associated tests, and model data for twitter/webpage
TWITTER_USERNAME_REGEX = re.compile("[a-zA-Z0-9_]+")
HTTP_S_REGEX = re.compile("https?://")
