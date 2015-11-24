from datetime import timedelta
from django.contrib.auth.models import User, Group, AnonymousUser
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth import logout
from django.views.generic import TemplateView, ListView, FormView, View, DetailView
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from kw_webapp import constants
from kw_webapp.models import Profile, UserSpecific, Vocabulary, Announcement
from kw_webapp.forms import UserCreateForm, SettingsForm
from rest_framework.renderers import JSONRenderer
from django.utils import timezone
from kw_webapp.serializers import UserSerializer, GroupSerializer, ReviewSerializer, ProfileSerializer
from kw_webapp.tasks import all_srs, unlock_eligible_vocab_from_level
import logging

logger = logging.getLogger("kw.views")
data_logger = logging.getLogger("kw.review_data")


class Settings(FormView):
    template_name = "kw_webapp/settings.html"
    form_class = SettingsForm

    def get_context_data(self, **kwargs):
        context = super(Settings, self).get_context_data()
        form = SettingsForm(instance=self.request.user.profile)
        context['form'] = form
        return context

    def form_valid(self, form):
        print(form.cleaned_data)
        data = form.cleaned_data
        self.request.user.profile.api_key = data['api_key']
        self.request.user.profile.save()
        logger.info("Saved Settings changes for {}.".format(self.request.user.username))
        return HttpResponseRedirect(reverse_lazy("kw:settings"))

    def form_invalid(self, form):
        print(form.cleaned_data)
        print(form.errors)
        return HttpResponseRedirect(reverse_lazy("kw:settings"))


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = UserSpecific.objects.all()
    serializer_class = ReviewSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        queryset = UserSpecific.objects.filter(user=user, needs_review=True)
        return queryset


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Profile.objects.filter(user=user)
        return queryset


class About(TemplateView):
    template_name = "kw_webapp/about.html"


class Contact(TemplateView):
    template_name = "kw_webapp/contact.html"


class Dashboard(TemplateView):
    template_name = "kw_webapp/home.html"

    def get_context_data(self, **kwargs):
        context = super(Dashboard, self).get_context_data()
        context['announcements'] = Announcement.objects.all().order_by('-pub_date')[:2]
        return context


class ForceSRSCheck(View):
    """
    temporary view that allows users to force an SRS update check on their account. Any thing that needs reviewing will
    added to the review queue.
    """

    def get(self, request, *args, **kwargs):
        user = request.user
        number_of_reviews = all_srs(user)
        new_review_count = UserSpecific.objects.filter(user=request.user, needs_review=True).count()
        logger.info("{} has requested an SRS update. {} reviews added. {} reviews total.".format(user.username,
                                                                                                 number_of_reviews or 0,
                                                                                                 new_review_count or 0))
        return HttpResponse(new_review_count)


class UnlockRequested(View):
    """
    Ajax-only view meant for unlocking previous levels. Post params: Level.
    """

    def post(self, request, *args, **kwargs):
        user = self.request.user
        requested_level = request.POST["level"]

        ul_count, l_count = unlock_eligible_vocab_from_level(user, requested_level)
        user.profile.unlocked_levels.get_or_create(level=requested_level)

        if l_count == 0:
            return HttpResponse("{} vocabulary unlocked".format(ul_count))
        else:
            return HttpResponse(
                "{} vocabulary unlocked.\nHowever, you still have {} vocabulary locked in WaniKani".format(ul_count,
                                                                                                           l_count))


class UnlockLevels(TemplateView):
    template_name = "kw_webapp/unlocklevels.html"

    def get_context_data(self, **kwargs):
        user_profile = self.request.user.profile
        context = super(UnlockLevels, self).get_context_data()
        level_status = []
        unlocked_levels = [item[0] for item in user_profile.unlocked_levels_list()]
        for level in range(1, 61):
            if level in unlocked_levels:
                level_status.append([level, True])
            else:
                level_status.append([level, False])

        context["levels"] = level_status
        return context


class Levels(TemplateView):
    template_name = "kw_webapp/levels.html"

    def get_context_data(self, **kwargs):
        user_profile = self.request.user.profile
        context = super(Levels, self).get_context_data()
        level_status = []
        unlocked_levels = [item[0] for item in user_profile.unlocked_levels_list()]
        for level in range(1, 61):
            if level in unlocked_levels:
                level_status.append([level, True])
            else:
                level_status.append([level, False])

        context["levels"] = level_status
        return context


class LevelVocab(TemplateView):
    template_name = "kw_webapp/levelvocab.html"

    def get_context_data(self, **kwargs):
        context = super(LevelVocab, self).get_context_data()
        level = self.kwargs['level']
        user = self.request.user
        level_vocab = UserSpecific.objects.filter(user=user, vocabulary__reading__level=level)
        context['reviews'] = level_vocab
        context['selected_level'] = level
        return context


class ToggleVocabLockStatus(View):
    """
    Ajax-only view that essentially flips the hidden status of a single vocabulary.
    """

    def post(self, request, *args, **kwargs):
        review_id = request.POST["review_id"]
        review = UserSpecific.objects.get(pk=review_id)
        review.hidden = not review.hidden
        review.save()
        return HttpResponse("Hidden From Reviews." if review.hidden else "Added to Review Queue.")


class RecordAnswer(View):
    """
    Called via Ajax in reviews.js. Takes a UserSpecific object, and either True or False. Updates the DB in realtime
    so that if the session crashes the review at least gets partially done.
    """
    srs_times = constants.SRS_TIMES

    def get(self, request, *args, **kwargs):
        logger.error("{} attempted to access RecordAnswer via a get!".format(request.user.username))
        return HttpResponseRedirect(reverse_lazy("kw:home"))

    def post(self, request, *args, **kwargs):
        us_id = request.POST["user_specific_id"]
        user_correct = True if request.POST['user_correct'] == 'true' else False
        previously_wrong = True if request.POST['wrong_before'] == 'true' else False
        us = get_object_or_404(UserSpecific, pk=us_id)
        data_logger.info(
            "{}|{}|{}|{}".format(us.user.username, us.vocabulary.meaning, user_correct, us.streak, us.synonyms))
        if user_correct:
            if not previously_wrong:
                us.correct += 1
                us.streak += 1
                if us.streak >= 9:
                    us.burnt = True
            us.needs_review = False
            us.last_studied = timezone.now()
            us.next_review_date = timezone.now() + timedelta(hours=RecordAnswer.srs_times[us.streak])
            us.save()
            return HttpResponse("Correct!")
        elif not user_correct:
            us.incorrect += 1
            if us.streak == 7:
                us.streak -= 2
            else:
                us.streak -= 1
            if us.streak < 0:
                us.streak = 0
            us.save()
            return HttpResponse("Incorrect!")
        else:
            logger.error(
                "{} managed to post some bad data to RecordAnswer: {}".format(request.user.username, request.POST))
            return HttpResponse("Error!")
        return HttpResponse("Error!")


class ReviewJson(View):
    # this may end up unnecessary. Not using it at trhe moment.
    def get(self, request, *args, **kwargs):
        user = request.user
        all_reviews = UserSpecific.objects.filter(user=user, needs_review=True)
        serializer = ReviewSerializer(all_reviews, many=True)
        return Response(serializer.data)


class Review(ListView):
    template_name = "kw_webapp/review.html"
    model = UserSpecific

    def get(self, request, *args, **kwargs):
        logger.info("{} has started a review session.".format(request.user.username))
        return super(Review, self).get(request)

    def get_context_data(self, **kwargs):
        context = super(Review, self).get_context_data()
        return context

    def get_queryset(self):
        user = self.request.user
        # ? randomizes the queryset.
        res = UserSpecific.objects.filter(user=user, needs_review=True, hidden=False).order_by('?')
        for re in res:
            print(re.synonym_set.all())
            print(re.synonyms_string())
            print(re.synonyms_list())
        return res


class ReviewSummary(TemplateView):
    template_name = "kw_webapp/reviewsummary.html"

    def get(self, request, *args, **kwargs):
        logger.warning("{} tried to GET ReviewSummary. Redirecting".format(request.user.username))
        return HttpResponseRedirect(reverse_lazy("kw:home"))

    def post(self, request, *args, **kwargs):
        logger.info("{} navigated to review summary page.".format(request.user.username))
        all_reviews = request.POST
        correct = []
        incorrect = []
        for us_id in all_reviews:
            try:
                if int(all_reviews[us_id]) > 0:
                    related_review = UserSpecific.objects.get(pk=us_id)
                    correct.append(related_review)
                elif int(all_reviews[us_id]) < 0:
                    related_review = UserSpecific.objects.get(pk=us_id)
                    incorrect.append(related_review)
                else:
                    # in case somehow the us_id value is zero. should be impossible.
                    logging.error("Un-parseable: {}".format(us_id))
            except ValueError as e:
                # this is here to catch the CSRF token essentially.
                logging.debug("Un-parseable: {}".format(us_id))
        # wow what a shit-ass hack. TODO figure out the proper way to render templates off a post.
        return render_to_response(self.template_name, {"correct": correct,
                                                       "incorrect": incorrect,
                                                       "correct_count": len(correct),
                                                       "incorrect_count": len(incorrect),
                                                       "review_count": len(correct) + len(incorrect)})


class Logout(TemplateView):
    def get(self, request, *args, **kwargs):
        logger.info("{} has requested a logout.".format(request.user.username))
        logout(request=request)
        return HttpResponseRedirect(reverse_lazy("kw:home"))


class Register(FormView):
    template_name = "registration/registration.html"
    form_class = UserCreateForm
    success_url = reverse_lazy("kw:home")

    def form_valid(self, form):
        user = form.save()
        logger.info("New User Created: {}, with API key {}.".format(user.username, form.cleaned_data['api_key']))
        Profile.objects.create(
            user=user, api_key=form.cleaned_data['api_key'], level=1)
        return HttpResponseRedirect(reverse_lazy("kw:home"))


def home(request):
    return HttpResponseRedirect(reverse_lazy('kw:home'))


