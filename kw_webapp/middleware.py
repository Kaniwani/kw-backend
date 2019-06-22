from django.utils import deprecation
from django.utils.timezone import now

from kw_webapp.models import Profile
from kw_webapp.tasks import past_time


class SetLastVisitMiddleware(deprecation.MiddlewareMixin):
    """
    A middleware class which will update a last_visit field in the profile once an hour.
    """

    buffer_hours = 1

    def process_response(self, request, response):
        if (
            hasattr(request, "user")
            and request.user.is_authenticated()
            and self.should_update(request.user)
        ):
            Profile.objects.filter(pk=request.user.profile.pk).update(
                last_visit=now()
            )
        return response

    def should_update(self, user):
        return (
            user.profile.last_visit is None
            or user.profile.last_visit <= past_time(self.buffer_hours)
        )
