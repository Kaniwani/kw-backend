import requests
from kw_webapp.models import Vocabulary

url = "https://www.wanikani.com/api/user/50f4abec6b4afdecdb892938e1193edb/vocabulary/{}"


def repopulate():
    for level in range(1, 51):
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
                for reading in kana:
                    new_vocab.reading_set.get_or_create(
                        kana=reading, character=character, level=level)
