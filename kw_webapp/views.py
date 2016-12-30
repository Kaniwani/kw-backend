import simplejson as simplejson
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, HttpResponseNotFound, JsonResponse, \
    Http404
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth import logout, authenticate, login
from django.views.generic import TemplateView, ListView, View
from django.views.generic.edit import FormView, UpdateView
from django.utils import timezone

from rest_framework import viewsets

from kw_webapp import constants
from kw_webapp.mixins import ValidApiRequiredMixin
from kw_webapp.models import Profile, UserSpecific, Announcement, AnswerSynonym
from kw_webapp.forms import UserCreateForm, SettingsForm
from kw_webapp.tasks import all_srs, unlock_eligible_vocab_from_levels, lock_level_for_user, \
    unlock_all_possible_levels_for_user, sync_user_profile_with_wk, sync_with_wk, get_wanikani_level_by_api_key, \
    get_users_current_reviews, \
    user_returns_from_vacation
from kw_webapp.wanikani import exceptions

logger = logging.getLogger("kw.views")
data_logger = logging.getLogger("kw.review_data")


class Settings(LoginRequiredMixin, UpdateView):
    template_name = "kw_webapp/settings.html"
    form_class = SettingsForm
    model = Profile

    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)

    def form_valid(self, form):
        # re-unlock current level is user now wants to be followed.
        # if not self.request.user.profile.follow_me and form.cleaned_data['follow_me']:
        was_following = self.request.user.profile.follow_me
        was_on_vacation = self.request.user.profile.on_vacation
        self.object = form.save(commit=False)
        self.object.api_valid = True
        user = User.objects.get(username=self.request.user.username)
        if not was_following and self.object.follow_me:  # if user swaps from non-following to following, sync them.
            try:
                self.object.level = get_wanikani_level_by_api_key(self.object.api_key)
                self.object.unlocked_levels.get_or_create(level=self.object.level)
                self.object.save()
                unlock_eligible_vocab_from_levels(self.object.user, self.object.level)
                sync_user_profile_with_wk(user)
            except exceptions.InvalidWaniKaniKey:
                user.profile.api_valid = False
                user.profile.save()

        else:
            self.object.save()

        if was_on_vacation and not self.object.on_vacation:
            user_returns_from_vacation(user)
        elif not was_on_vacation and self.object.on_vacation:
            user.profile.vacation_date = timezone.now()
            user.profile.save()

        logger.info("Saved Settings changes for {}.".format(self.request.user.username))
        return HttpResponseRedirect(reverse_lazy("kw:settings"))

    def form_invalid(self, form, **kwargs):
        context = self.get_context_data(**kwargs)
        print(form.errors)
        context['form'] = form
        return self.render_to_response(context)

class About(LoginRequiredMixin, TemplateView):
    template_name = "kw_webapp/about.html"


class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = "kw_webapp/home.html"

    def get_context_data(self, **kwargs):
        context = super(Dashboard, self).get_context_data()
        context['announcements'] = Announcement.objects.all().order_by('-pub_date')[:5]
        return context


class ForceSRSCheck(LoginRequiredMixin, View):
    """
    temporary view that allows users to force an SRS update check on their account. Any thing that needs reviewing will
    added to the review queue.
    """

    def get(self, request, *args, **kwargs):
        user = request.user
        number_of_reviews = all_srs(user)
        new_review_count = get_users_current_reviews(user).count()
        logger.info("{} has requested an SRS update. {} reviews added. {} reviews total.".format(user.username,
                                                                                                 number_of_reviews or 0,
                                                                                                 new_review_count or 0))
        return HttpResponse(new_review_count)


class LockRequested(LoginRequiredMixin, View):
    """
    AJAX-only view for locking an entire level at a time. Blows away the user's review information for every
    """

    def post(self, request, *args, **kwargs):
        user = self.request.user
        requested_level = request.POST['level']
        # if user locks their current level, prevent WK syncing new stuff.
        if user.profile.level == int(requested_level):
            user.profile.follow_me = False
            user.profile.save()
        removed_count = lock_level_for_user(requested_level, user)

        return HttpResponse("{} items removed from your study queue.".format(removed_count))


class UnlockAll(LoginRequiredMixin, ValidApiRequiredMixin, View):
    """
    Ajax-only view unlocking ALL previous levels. The nuclear option, as it were.
    """

    def post(self, request, *args, **kwargs):
        should_sync = False
        user = self.request.user
        lower_level_range = [level for level in range(1, user.profile.level + 1)]
        for level in lower_level_range:
            if level not in user.profile.unlocked_levels_list():
                should_sync = True
                user.profile.unlocked_levels.get_or_create(level=level)

        if should_sync:
            level_list, unlocked_now, unlocked_total, locked_count = unlock_all_possible_levels_for_user(user)
            return HttpResponse("Unlocked {} levels, containing {} vocabulary.".format(len(level_list), unlocked_now))
        else:
            return HttpResponse("Everything has already been unlocked!")


class UnlockRequested(LoginRequiredMixin, ValidApiRequiredMixin, View):
    """
    Ajax-only view meant for unlocking previous levels. Post params: Level.
    """

    def post(self, request, *args, **kwargs):
        user = self.request.user
        requested_level = request.POST["level"]

        if int(requested_level) > user.profile.level:
            return HttpResponseForbidden()

        ul_count,total_unlocked, l_count = unlock_eligible_vocab_from_levels(user, requested_level)
        user.profile.unlocked_levels.get_or_create(level=requested_level)

        if l_count == 0:
            return HttpResponse("{} vocabulary unlocked".format(ul_count))
        else:
            return HttpResponse(
                "{} vocabulary unlocked.<br/>You still have {} upcoming vocabulary to unlock on WaniKani for your current level.".format(
                    ul_count,
                    l_count))


class SyncRequested(LoginRequiredMixin, View):
    """
    Ajax view so that the user can request a sync of their profile and vocabulary
    """

    def get(self, request, *args, **kwargs):
        logger.debug("Entering SyncRequrested for user {}".format(self.request.user))
        should_full_sync = simplejson.loads(request.GET.get("full_sync", "false"))
        profile_sync_succeeded, new_review_count, new_synonym_count = sync_with_wk(self.request.user.id, should_full_sync)
        logger.debug("Exiting SyncRequested for user {}".format(self.request.user))
        return JsonResponse({"profile_sync_succeeded": profile_sync_succeeded,
                             "new_review_count": new_review_count,
                             "new_synonym_count": new_synonym_count})


class UnlockLevels(LoginRequiredMixin, TemplateView):
    template_name = "kw_webapp/vocabulary.html"

    def get_context_data(self, **kwargs):
        user_profile = self.request.user.profile
        context = super(UnlockLevels, self).get_context_data()
        level_status = []
        unlocked_levels = user_profile.unlocked_levels_list()
        for level in range(1, 61):
            if level in unlocked_levels:
                level_status.append([level, True])
            else:
                level_status.append([level, False])

        context["levels"] = level_status
        return context


class SRSVocab(LoginRequiredMixin, TemplateView):
    template_name = "kw_webapp/levelvocab.html"

    def get_context_data(self, **kwargs):
        context = super(SRSVocab, self).get_context_data()
        requested_srs_level = self.kwargs['srs_level']

        if requested_srs_level not in constants.KANIWANI_SRS_LEVELS:
            raise Http404

        related_levels = constants.KANIWANI_SRS_LEVELS[requested_srs_level]

        user = self.request.user
        vocab = UserSpecific.objects.filter(user=user, streak__in=related_levels).distinct().order_by(
            "vocabulary__meaning")
        context['reviews'] = vocab
        context['selected_level'] = requested_srs_level
        return context


class LevelVocab(LoginRequiredMixin, TemplateView):
    template_name = "kw_webapp/levelvocab.html"

    def get_context_data(self, **kwargs):
        context = super(LevelVocab, self).get_context_data()
        level = self.kwargs['level']
        user = self.request.user
        level_vocab = UserSpecific.objects.filter(user=user, vocabulary__readings__level=level).distinct().order_by(
            "vocabulary__meaning")
        context['reviews'] = level_vocab
        context['selected_level'] = level
        return context


class Error404(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        response = render(template_name="404.html", status=404)
        return HttpResponseNotFound(response)


class ToggleVocabLockStatus(LoginRequiredMixin, View):
    """
    Ajax-only view that essentially flips the hidden status of a single vocabulary.
    """

    def post(self, request, *args, **kwargs):
        review_id = request.POST["review_id"]
        review = UserSpecific.objects.get(pk=review_id)
        if review.can_be_managed_by(self.request.user):
            review.hidden = not review.hidden
            review.save()
            return HttpResponse("Hidden From Reviews." if review.hidden else "Added to Review Queue.")
        else:
            return HttpResponseForbidden()


class RemoveSynonym(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        synonym_id = request.POST['synonym_id']
        synonym = get_object_or_404(AnswerSynonym, pk=synonym_id)
        response_string = "Synonym {}/{} deleted".format(synonym.kana, synonym.character)
        synonym.delete()
        return HttpResponse(response_string)


class AddSynonym(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponseForbidden()

    def post(self, request, *args, **kwargs):
        review_id = request.POST["user_specific_id"]
        review = get_object_or_404(UserSpecific, pk=review_id)

        if not review.can_be_managed_by(self.request.user):
            return HttpResponseForbidden("You can't modify that object!")

        synonym_kana = request.POST["kana"]
        synonym_kanji = request.POST["kanji"]
        synonym, successfully_added = review.add_answer_synonym(synonym_kana, synonym_kanji)

        return JsonResponse(synonym.as_dict())


class RecordAnswer(LoginRequiredMixin, View):
    """
    Called via Ajax in reviews.js. Takes a UserSpecific object, and either True or False. Updates the DB in realtime
    so that if the session crashes the review at least gets partially done.
    """
    srs_times = constants.SRS_TIMES

    def get(self, request, *args, **kwargs):
        logger.error("{} attempted to access RecordAnswer via a get!".format(request.user.username))
        return HttpResponseRedirect(reverse_lazy("kw:home"))

    def post(self, request, *args, **kwargs):
        review_id = request.POST["user_specific_id"]
        user_correct = True if request.POST['user_correct'] == 'true' else False
        previously_wrong = True if request.POST['wrong_before'] == 'true' else False
        review = get_object_or_404(UserSpecific, pk=review_id)

        if not review.can_be_managed_by(self.request.user) or not review.needs_review:
            return HttpResponseForbidden("You can't modify that object at this time!")

        data_logger.info(
            "{}|{}|{}|{}".format(review.user.username, review.vocabulary.meaning, user_correct, review.streak,
                                 review.synonyms_string()))
        if user_correct:
            if not previously_wrong:
                review.correct += 1
                review.streak += 1
                if review.streak >= 9:
                    review.burned = True
            review.needs_review = False
            review.last_studied = timezone.now()
            review.save()
            review.set_next_review_time()
            return HttpResponse("Correct!")
        elif not user_correct:
            review.incorrect += 1
            if review.streak == 7:
                review.streak -= 2
            else:
                review.streak -= 1
            if review.streak < 0:
                review.streak = 0
            review.save()
            return HttpResponse("Incorrect!")
        else:
            logger.error(
                "{} managed to post some bad data to RecordAnswer: {}".format(request.user.username, request.POST))
            return HttpResponse("Error!")
        return HttpResponse("Error!")


class Review(LoginRequiredMixin, ListView):
    template_name = "kw_webapp/review.html"
    model = UserSpecific

    def get(self, request, *args, **kwargs):
        logger.info("{} has started a review session.".format(request.user.username))
        if get_users_current_reviews(self.request.user).count() < 1:
            return HttpResponseRedirect(reverse_lazy("kw:home"))
        else:
            return super(Review, self).get(request)

    def get_queryset(self):
        user = self.request.user
        res = get_users_current_reviews(user).order_by('?')[:300]
        return res


class ReviewSummary(LoginRequiredMixin, TemplateView):
    template_name = "kw_webapp/reviewsummary.html"

    def get(self, request, *args, **kwargs):
        logger.warning("{} tried to GET ReviewSummary. Redirecting".format(request.user.username))
        return HttpResponseRedirect(reverse_lazy("kw:home"))

    def post(self, request, *args, **kwargs):
        logger.info("{} navigated to review summary page.".format(request.user.username))

        all_reviews = request.POST

        if len(all_reviews) <= 1:
            # The post data is only populated by the CSRF token. No reviews were done
            return HttpResponseRedirect(reverse_lazy("kw:home"))

        correct = []
        incorrect = []

        for review_id in all_reviews:
            try:
                if int(all_reviews[review_id]) > 0:
                    related_review = UserSpecific.objects.get(pk=review_id)
                    correct.append(related_review)
                elif int(all_reviews[review_id]) < 0:
                    related_review = UserSpecific.objects.get(pk=review_id)
                    incorrect.append(related_review)
                else:
                    # in case somehow the review_id value is zero. should be impossible.
                    logging.error("Un-parseable: {}".format(review_id))
            except ValueError as e:
                # this is here to catch the CSRF token essentially.
                logging.debug("Un-parseable: {}".format(review_id))

        return render(request, self.template_name, {"correct": correct,
                                                    "incorrect": incorrect,
                                                    "correct_count": len(correct),
                                                    "incorrect_count": len(incorrect),
                                                    "review_session_count": len(correct) + len(incorrect)})


class Logout(LoginRequiredMixin, TemplateView):
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

        sync_with_wk(user.id)
        user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
        login(self.request, user)
        return HttpResponseRedirect(reverse_lazy("kw:home"))


class Sent(TemplateView):
    template_name = "contact_form/contact_form_sent.html"


@login_required()
def home(request):
    return HttpResponseRedirect(reverse_lazy('kw:home'))
