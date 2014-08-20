from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth import logout
from django.utils.encoding import smart_str
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


class UnlockLevels(TemplateView):
    template_name = "kw_webapp/unlocklevels.html"

    def get_context_data(self, **kwargs):
        user_profile = self.request.user.profile
        context = super(UnlockLevels, self).get_context_data()
        unlocked = []
        locked = []
        print("TEST")
        #print(user_profile.unlocked_levels)
        for level in range(0, 51):

            if level in user_profile.unlocked_levels_list():
                unlocked.append(level)
            else:
                locked.append(level)

        context["locked"] = locked
        context["unlocked"] = unlocked
        return context


class RecordAnswer(View):
    """
    Called via Ajax in reviews.js. Takes a UserSpecific object, and either True or False. Updates the DB in realtime
    so that if the session crashes the review at least gets partially done.
    """
    def get(self, request, *args, **kwargs):
        logger.info("Can't access RecordAnswer via a get!")
        return HttpResponseRedirect(reverse_lazy("kw:home"))

    def post(self, request, *args, **kwargs):
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


class ReviewSummary(TemplateView):
    template_name = "kw_webapp/reviewsummary.html"
    correct = []
    incorrect = []

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse_lazy("kw:home"))

    def post(self, request, *args, **kwargs):
        all_reviews = request.POST

        for vocab_meaning in all_reviews:
            if all_reviews[vocab_meaning] == "true":
                self.correct.append(vocab_meaning)
            elif all_reviews[vocab_meaning] == "false":
                self.incorrect.append(vocab_meaning)
            else:
                print("Unparseable: {}".format(vocab_meaning))
        #wow what a shit-ass hack. TODO figure out the proper way to render templates off a post. 
        return render_to_response(self.template_name, {"correct":self.correct, "incorrect":self.incorrect})


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
        return HttpResponseRedirect(reverse_lazy("kw:home"))


def home(request):
    return HttpResponseRedirect(reverse_lazy('kw:home'))
