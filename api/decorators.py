
from functools import wraps

from wanikani_api.exceptions import InvalidWanikaniApiKeyException

from api.responses import InvalidWanikaniAPIKeyResponse
from kw_webapp.wanikani.exceptions import InvalidWaniKaniKey

def checks_wanikani(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        # Currently, depending on whether v1 or v2 throws an error, a uniquely
        # named error is thrown. Eventually when wanikani_api is retrofitted to support
        # V1, these will be merged.
        except InvalidWaniKaniKey or InvalidWanikaniApiKeyException:
            request = args[1]
            profile = request.user.profile
            profile.api_valid = False
            profile.save()
            return InvalidWanikaniAPIKeyResponse()

    return wrapper

