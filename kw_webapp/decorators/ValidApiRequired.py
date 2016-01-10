from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse_lazy


def valid_api_required(function=None):
    actual_decorator = user_passes_test(lambda u: u.profile.api_valid, login_url=reverse_lazy('kw:settings'))
    if function:
        return actual_decorator(function)
    return actual_decorator
