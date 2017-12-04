from django.contrib.auth.mixins import AccessMixin
from django.core.urlresolvers import reverse_lazy


class ValidApiRequiredMixin(AccessMixin):
    """
    CBV mixin for verifying that a user has a valid Wanikani key before we attempt to make any API calls.
    """
    invalid_api_redirect_url = reverse_lazy("kw:settings")
    permission_denied_message = "Your Wanikani API key is invalid! Please change it in the settings"
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        if not request.user.profile.api_valid:
            return self.handle_no_permission()
        return super(ValidApiRequiredMixin, self).dispatch(request, *args, **kwargs)