from django.utils.timezone import now
from kw_webapp.models import Profile
from kw_webapp.tasks import past_time



class SetLastVisitMiddleware:
    """
    A middleware class which will update a last_visit field in the profile once an hour.
    """
    buffer_hours = 1

    def process_response(self, request, response):
        if request.user.is_authenticated() and request.user.profile.last_visit <= past_time(self.buffer_hours):
            print("UPDATING USER LAST VISIT TO " + str(now()))
            Profile.objects.filter(pk=request.user.profile.pk).update(last_visit=now())
        return response
