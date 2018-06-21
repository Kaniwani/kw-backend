from . import constants


class WanikaniAPIException(Exception):
    pass


class InvalidWaniKaniKey(WanikaniAPIException):
    pass


class InvalidArguments(WanikaniAPIException):
    pass


ExceptionSelector = {
    constants.INVALID_WK_API_ERROR: InvalidWaniKaniKey,
    constants.INVALID_ARGUMENTS_ERROR: InvalidArguments,
}
