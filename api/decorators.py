
from functools import wraps

from api.responses import InvalidWanikaniAPIKeyResponse
from kw_webapp.wanikani.exceptions import InvalidWaniKaniKey

def checks_wanikani(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except InvalidWaniKaniKey:
            request = args[1]
            profile = request.user.profile
            profile.api_valid = False
            profile.save()
            return InvalidWanikaniAPIKeyResponse()

    return wrapper

