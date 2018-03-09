import requests
import logging
from . import constants
from . import exceptions

logger = logging.getLogger(__name__)


def _has_no_errors(response):
    return response and "error" not in response.json() and response.status_code == 200


def _has_invalid_key_error(response):
    response = response.json()
    error_details = response['error']
    return error_details['code'] == constants.INVALID_WK_API_ERROR


def _get_error(response):
    response = response.json()
    error_details = response['error']
    error_code = error_details['code']
    error_message = error_details['message']

    if error_code in exceptions.ExceptionSelector:
        error = exceptions.ExceptionSelector[error_code]
        return error(error_message)
    else:
        return exceptions.WanikaniAPIException(error_details['message'])




def make_api_call(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()

    if response.status_code == 401:
        raise exceptions.InvalidWaniKaniKey("Got a 401 from Wanikani!")
