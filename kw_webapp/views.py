from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth import logout
from django.views.generic import TemplateView, ListView, FormView, View
from kw_webapp.models import Profile, UserSpecific
from kw_webapp.forms import UserCreateForm
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import logging

logger = logging.getLogger("kw_webapp.views")


class Dashboard(TemplateView):
    template_name = "kw_webapp/home.html"

    def get_context_data(self, **kwargs):
        context = super(Dashboard, self).get_context_data()
        context['review_count'] = UserSpecific.objects.filter(user=self.request.user, needs_review=True).count()
        return context



@csrf_exempt
def RecordAnswer(request):
    if request.method == "POST":
        us_id = request.POST["user_specific_id"]
        user_correct = request.POST["user_correct"]
        us = get_object_or_404(UserSpecific, pk=us_id)
        logger.info("Recording Answer.On usid:{} the correctness was {}".format(us, user_correct))
        if user_correct == "true":
            us.correct += 1
            us.streak += 1
            us.needs_review = False
            us.last_studied = timezone.now()
            us.save()
            return HttpResponse("Correct!")
        elif user_correct == "false":
            us.incorrect += 1
            us.streak -= 1
            if us.streak < 0:
                us.streak = 0
            us.save()
            return HttpResponse("Incorrect!")



class Review(ListView):
    template_name = "kw_webapp/review.html"
    model = UserSpecific

    def get_context_data(self, **kwargs):
        context = super(Review, self).get_context_data()
        user = self.request.user
        # this may end up unnecessary. Not using it at the moment.
        context["json"] = serializers.serialize(
            "json", UserSpecific.objects.filter(user=user, needs_review=True))

        print(context['json'])
        return context

    def get_queryset(self):
        user = self.request.user
        res = UserSpecific.objects.filter(user=user, needs_review=True).order_by('?')
        return res


class ReviewSummary(View):
    template_name = "kw_webapp/reviewsummary.html"

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse_lazy("kw:dashboard"))

    def post(self, request, *args, **kwargs):
        correctly_reviewed = request.POST.get("correct_answers", False)
        incorrectly_reviewed = request.POST.get("incorrect_answers", False)
        print(correctly_reviewed)
        print(incorrectly_reviewed)
        print(request.POST)




class Logout(TemplateView):

    def get(self, request, *args, **kwargs):
        logout(request=request)
        return HttpResponseRedirect(reverse_lazy("kw:home"))


class Register(FormView):
    template_name = "registration/registration.html"
    form_class = UserCreateForm
    success_url = reverse_lazy("kw:home")

    def form_valid(self, form):
        user = form.save()
        Profile.objects.create(
            user=user, api_key=form.cleaned_data['api_key'], level=1)
        return HttpResponseRedirect(reverse_lazy("kw:dashboard"))


def home(request):
    return HttpResponseRedirect(reverse_lazy('kw:dashboard'))
