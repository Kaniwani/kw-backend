import requests
from rest_framework import serializers
from wanikani_api.client import Client as WkV2Client
from wanikani_api.exceptions import InvalidWanikaniApiKeyException
import logging

logger = logging.getLogger(__name__)

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
            logger.debug(f"We have validated API V2 Key {value}")
            return value
        except InvalidWanikaniApiKeyException:
            logger.debug(f"We failed to validate API V2 Key {value}")
            raise serializers.ValidationError(self.failure_message)
