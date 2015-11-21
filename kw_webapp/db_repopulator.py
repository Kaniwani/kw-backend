import requests
import logging
from kw_webapp.models import Vocabulary

url = "https://www.wanikani.com/api/user/99c4bab4d2c59ad514e2a7105fbb3bf7/vocabulary/{}"

logger = logging.getLogger("kw.db_repopulator")


def repopulate():
    logger.info("Staring DB Repopulation from WaniKani")
    for level in range(1, 61):
        r = requests.get(
            url.format(level))
        if r.status_code == 200:
            json_data = r.json()
            vocabulary_list = json_data['requested_information']
            for vocabulary in vocabulary_list:
                character = vocabulary["character"]
                kana = [reading.strip() for reading in vocabulary["kana"].split(",")]#Splits out multiple readings for one vocab.
                meaning = vocabulary["meaning"]
                level = vocabulary["level"]
                new_vocab, created = Vocabulary.objects.get_or_create(
                    meaning=meaning)
                if created:
                    logger.info("Found new Vocabulary item from WaniKani:{}".format(new_vocab.meaning))
                for reading in kana:
                    new_reading, created = new_vocab.reading_set.get_or_create(
                        kana=reading, character=character, level=level)
                    if created:
                        logger.info("""Created new reading: {}, level {}
                                     associated to vocab {}""".format(new_reading.kana,new_reading.level, new_reading.vocabulary.meaning))
        else:
            logger.error("Status code returned from WaniKani API was not 200! It was {}".format(r.status_code))
