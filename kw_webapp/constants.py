SRS_TIMES = {
    0: 4,  # Apprentice
    1: 4,  # Apprentice
    2: 8,  # Apprentice
    3: 24,  # Guru
    4: 72,  # Guru
    5: 168,  # Guru
    6: 336,  # Master
    7: 720,  # Master
    8: 2160,  # Enlightened
    9: 4320,  # Burned
}

# The level arrangement I believe to be exposed by WK API.
WANIKANI_SRS_LEVELS = {
    "apprentice": [0, 1, 2, 3, 4],
    "guru": [5, 6],
    "master": [7],
    "enlightened": [8],
    "burned": [9]
}

LEVEL_MIN = 1
LEVEL_MAX = 60
API_KEY = "67f0c45687b8079a316a29dc3cbd5a40"
