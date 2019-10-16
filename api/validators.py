import requests
from rest_framework import serializers
from wanikani_api.client import Client as WkV2Client
from wanikani_api.exceptions import InvalidWanikaniApiKeyException
import logging

logger = logging.getLogger(__name__)


class WanikaniApiKeyValidatorV1(object):
    def __init__(self):
        self.failure_message = "This API key appears to be invalid"

    def __call__(self, value):
        logger.debug(f"We are validating API V1 Key {value}")
        api_string = self.build_v1_user_information_api_string(value)
        r = requests.get(api_string)
        if r.status_code == 200:
            json_data = r.json()
            # WK Seems to often change what their failure state is, lets check instead for positive state.
            if "user_information" in json_data.keys():
                logger.debug(f"We have valiated API V1 Key {value}")
                return value

        logger.debug(f"We failed to validate API V2 Key {value}")
        raise serializers.ValidationError(self.failure_message)

    def build_v1_user_information_api_string(self, api_key):
        return f"https://www.wanikani.com/api/user/{api_key}/user-information"


class WanikaniApiKeyValidatorV2(object):
    def __init__(self):
        self.failure_message = "This V2 API key appears to be invalid"

    def __call__(self, value):
        logger.debug(f"We are validating API V2 Key {value}")
        if not value or value == "None":
            return None
        client = WkV2Client(value)
        try:
            client.user_information()
            logger.debug(f"We have valiated API V2 Key {value}")
            return value
        except InvalidWanikaniApiKeyException:
            logger.debug(f"We failed to validate API V2 Key {value}")
            raise serializers.ValidationError(self.failure_message)
