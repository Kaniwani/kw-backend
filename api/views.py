from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from rest_framework import generics, filters
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.reverse import reverse_lazy

from api.filters import VocabularyFilter, ReviewFilter
from api.permissions import IsAdminOrReadOnly, IsAuthenticatedOrCreating, IsAdminOrAuthenticatedAndCreating
from api.serializers import ReviewSerializer, VocabularySerializer, StubbedReviewSerializer, \
    HyperlinkedVocabularySerializer, ReadingSerializer, LevelSerializer, ReadingSynonymSerializer, \
    FrequentlyAskedQuestionSerializer, AnnouncementSerializer, UserSerializer, ContactSerializer, ProfileSerializer, \
    ReportSerializer, ReportCountSerializer, ReportListSerializer, MeaningSynonymSerializer, RegistrationSerializer
from kw_webapp import constants
from kw_webapp.forms import UserContactCustomForm
from kw_webapp.models import Vocabulary, UserSpecific, Reading, Level, AnswerSynonym, FrequentlyAskedQuestion, \
    Announcement, Profile, Report, MeaningSynonym
from kw_webapp.tasks import get_users_current_reviews, unlock_eligible_vocab_from_levels, lock_level_for_user, \
    get_users_critical_reviews, sync_with_wk, all_srs, sync_user_profile_with_wk, user_returns_from_vacation, \
    user_begins_vacation, follow_user, reset_user, get_users_lessons


from KW.LoggingMiddleware import RequestLoggingMixin
import logging
logger = logging.getLogger(__name__)


class ListRetrieveUpdateViewSet(mixins.ListModelMixin,
                                mixins.UpdateModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    """
    A viewset that provides `List`, `Update`, and `Retrieve` actions.
    Must override: .queryset, .serializer_class
    """
    pass


class ReadingViewSet(RequestLoggingMixin, viewsets.ReadOnlyModelViewSet):
    """
    For internal use fetching readings specifically.
    """
    queryset = Reading.objects.all()
    serializer_class = ReadingSerializer


class ReadingSynonymViewSet(RequestLoggingMixin, viewsets.ModelViewSet):
    serializer_class = ReadingSynonymSerializer

    def get_queryset(self):
        return AnswerSynonym.objects.filter(review__user=self.request.user)


class MeaningSynonymViewSet(RequestLoggingMixin, viewsets.ModelViewSet):
    serializer_class = MeaningSynonymSerializer

    def get_queryset(self):
        return MeaningSynonym.objects.filter(review__user=self.request.user)


class LevelViewSet(RequestLoggingMixin, viewsets.ReadOnlyModelViewSet):
    """
    Return a list of all levels and related information.

    unlock:
    Unlock the given level for a particular user. This will add all the vocabulary of that level to their review queue immediately

    lock:
    Lock the given level for a particular user. This will wipe away ALL related SRS information for these vocabulary as well.
    """
    queryset = Level.objects.all()
    serializer_class = LevelSerializer

    def get_object(self):
        level = int(self.kwargs['pk'])
        return self._serialize_level(level, self.request)

    def _serialize_level(self, level, request):
        unlocked = True if level in request.user.profile.unlocked_levels_list() else False
        level_obj = request.user.profile.unlocked_levels.get(level=level) if unlocked else None

        pre_serialized_dict = {'level': level,
                               'unlocked': unlocked,
                               'vocabulary_count': Vocabulary.objects.filter(readings__level=level).distinct().count(),
                               'vocabulary_url': level}
        if level <= request.user.profile.level:
            pre_serialized_dict['lock_url'] = self._build_lock_url(level)
            pre_serialized_dict['unlock_url'] = self._build_unlock_url(level)

        return pre_serialized_dict

    def list(self, request, *args, **kwargs):
        level_dicts = []
        for level in range(constants.LEVEL_MIN, constants.LEVEL_MAX + 1):
            level_dicts.append(self._serialize_level(level, request))

        serializer = LevelSerializer(level_dicts, many=True, context={'request': request})
        return Response(serializer.data)

    def _build_lock_url(self, level):
        return reverse_lazy('api:level-lock', args=(level,))

    def _build_unlock_url(self, level):
        return reverse_lazy('api:level-unlock', args=(level,))

    @detail_route(methods=['POST'])
    def unlock(self, request, pk=None):
        user = self.request.user
        requested_level = pk
        if int(requested_level) > user.profile.level:
            return Response(status=status.HTTP_403_FORBIDDEN)

        unlocked_this_request, total_unlocked, locked = unlock_eligible_vocab_from_levels(user, requested_level)
        user.profile.unlocked_levels.get_or_create(level=requested_level)

        return Response(dict(unlocked_now=unlocked_this_request,
                             total_unlocked=total_unlocked,
                             locked=locked))

    @detail_route(methods=['POST'])
    def lock(self, request, pk=None):
        requested_level = pk
        if request.user.profile.level == int(requested_level):
            request.user.profile.follow_me = False
            request.user.profile.save()
        removed_count = lock_level_for_user(requested_level, request.user)

        return Response({"locked": removed_count})


class VocabularyViewSet(RequestLoggingMixin, viewsets.ReadOnlyModelViewSet):
    """
    Endpoint for fetching specific vocabulary. You can pass parameter `hyperlink=true` to receive the vocabulary with
    hyperlinked readings (for increased performance), or else they will be inline
    """
    filter_class = VocabularyFilter
    queryset = Vocabulary.objects.all()

    def get_serializer_class(self):
        if self.request.query_params.get('hyperlink', 'false') == 'true':
            return HyperlinkedVocabularySerializer
        else:
            return VocabularySerializer


class ReportViewSet(RequestLoggingMixin, viewsets.ModelViewSet):
    filter_fields = ('created_by', 'reading')
    serializer_class = ReportSerializer
    permission_classes = (IsAdminOrAuthenticatedAndCreating,)

    @list_route(methods=["GET"])
    def counts(self, request):
        serializer = ReportCountSerializer(Report.objects.all())
        return Response(serializer.data)

    def get_queryset(self):
        if self.request.user.is_staff:
            return Report.objects.all()
        else:
            return Report.objects.filter(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Create a new report, or if an identical report already exists, update the existing one.
        """
        try:
            reading_id = request.data["reading"]
            existing_report = Report.objects.get(reading__id=reading_id, created_by=request.user)
            logger.info("User {} is updating their report on reading {}".format(request.user.username, request.data["reading"]))
            serializer = ReportSerializer(existing_report, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except Report.DoesNotExist:
            logger.info("User {} is creating report on reading {}".format(request.user.username, request.data["reading"]))
            serializer = ReportSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(created_by=self.request.user)
            return Response(serializer.data)

    def get_serializer_class(self):
        if self.action == "list":
            return ReportListSerializer
        return super().get_serializer_class()

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ReviewViewSet(RequestLoggingMixin, ListRetrieveUpdateViewSet):
    """
    lesson:
    Get all of user's lessons.

    current:
    Get all of user's reviews which currently need to be done.

    critical:
    Return a list of *critical* items, which the user has often gotten incorrect.

    correct:
    POSTing here will indicate that the user has successfully answered the review.

    incorrect:
    POSTing here will indicate that the user has incorrectly answered the review.

    hide:
    No longer include this item in the SRS algorithm and review queue.

    unhide:
    include this item in the SRS algorithm and review queue.
    """
    serializer_class = ReviewSerializer
    filter_class = ReviewFilter
    permission_classes = (IsAuthenticated,)

    @list_route(methods=['GET'])
    def lesson(self, request):
        lessons = get_users_lessons(request.user)
        page = self.paginate_queryset(lessons)
        if page is not None:
            serializer = StubbedReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = StubbedReviewSerializer(lessons, many=True)
        return Response(serializer.data)

    @list_route(methods=['GET'])
    def current(self, request):
        reviews = get_users_current_reviews(request.user)
        page = self.paginate_queryset(reviews)

        if page is not None:
            serializer = StubbedReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = StubbedReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @list_route(methods=['GET'])
    def critical(self, request):
        critical_reviews = get_users_critical_reviews(request.user)
        page = self.paginate_queryset(critical_reviews)

        if page is not None:
            serializer = ReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ReviewSerializer(critical_reviews, many=True)
        return Response(serializer.data)

    def _correct_on_first_try(self, request):
        if "wrong_before" not in request.data:
            return True
        if request.data["wrong_before"] is False:
            return True
        if request.data["wrong_before"] == "false":
            return True

        return False

    @detail_route(methods=['POST'])
    def correct(self, request, pk=None):
        review = get_object_or_404(UserSpecific, pk=pk)
        if not review.can_be_managed_by(request.user) or not review.needs_review:
            return HttpResponseForbidden("You can't modify that object at this time!")

        was_correct_on_first_try = self._correct_on_first_try(request)
        review = review.answered_correctly(was_correct_on_first_try)
        serializer = self.get_serializer(review, many=False)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def incorrect(self, request, pk=None):
        review = get_object_or_404(UserSpecific, pk=pk)
        if not review.can_be_managed_by(request.user) or not review.needs_review:
            return HttpResponseForbidden("You can't modify that object at this time!")
        review = review.answered_incorrectly()
        serializer = self.get_serializer(review, many=False)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def hide(self, request, pk=None):
        return self._set_hidden(request, True, pk)

    @detail_route(methods=['POST'])
    def unhide(self, request, pk=None):
        return self._set_hidden(request, False, pk)

    def _set_hidden(self, request, should_hide, pk=None):
        review = get_object_or_404(UserSpecific, pk=pk)
        if not review.can_be_managed_by(request.user):
            return HttpResponseForbidden("You can't modify that object!")

        review.hidden = should_hide
        review.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        return UserSpecific.objects.filter(user=self.request.user,
                                           wanikani_srs_numeric__gte=self.request.user.profile.get_minimum_wk_srs_threshold_for_review())


class FrequentlyAskedQuestionViewSet(RequestLoggingMixin, viewsets.ModelViewSet):
    """
    Frequently Asked Questions that uses will have read access to.
    """
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = FrequentlyAskedQuestionSerializer
    queryset = FrequentlyAskedQuestion.objects.all()


class AnnouncementViewSet(RequestLoggingMixin, viewsets.ModelViewSet):
    """
    Announcements that users will see upon entering the website.
    """
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.all().order_by('-pub_date')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class UserViewSet(RequestLoggingMixin, viewsets.GenericViewSet, generics.ListCreateAPIView):
    """
    Endpoint for user and internally nested profiles. Used primarily for updating user profiles, and creation of users.

    me:
    Standard endpoint to retrieve current user based on their authentication provided in the request. This is also where
    we PUT changes to the nested profile.

    sync:
    Force a sync to the Wanikani server.

    srs:
    Force an SRS run (typically runs every 15 minutes anyhow).

    reset:
    Reset a user's account. Removes all reviews, re-locks all levels. Immediately runs unlock on current level afterwards.
    """
    permission_classes = (IsAuthenticatedOrCreating,)
    serializer_class = UserSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()

        return User.objects.filter(pk=self.request.user.id)

    @list_route(methods=["GET"])
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user, many=False)
        return Response(serializer.data)

    @list_route(methods=['POST'])
    def sync(self, request):
        should_full_sync = False
        if 'full_sync' in request.data:
            should_full_sync = request.data['full_sync'] == 'true'

        profile_sync_succeeded, new_review_count, new_synonym_count = sync_with_wk(request.user.id, should_full_sync)
        return Response({"profile_sync_succeeded": profile_sync_succeeded,
                         "new_review_count": new_review_count,
                         "new_synonym_count": new_synonym_count})

    @list_route(methods=['POST'])
    def srs(self, request):
        all_srs(request.user)
        new_review_count = get_users_current_reviews(request.user).count()
        return Response({'review_count': new_review_count})

    @list_route(methods=['POST'])
    def reset(self, request):
        reset_to_level = int(request.data['level']) if 'level' in request.data else None
        if reset_to_level is None:
            return HttpResponseBadRequest("You must pass a level to reset to.")

        reset_user(request.user, reset_to_level)
        return Response({"message": "Your account has been reset"})


class ProfileViewSet(RequestLoggingMixin, ListRetrieveUpdateViewSet, viewsets.GenericViewSet):
    """
    Profile model view set, for INTERNAL TESTING USE ONLY.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

    def perform_update(self, serializer):

        serializer = self._update_calculated_fields(serializer)
        instance = serializer.save()
        return Response(instance)

    def _update_calculated_fields(self, serializer):
        old_instance = serializer.instance

        user = old_instance.user

        if old_instance.on_vacation and not serializer.validated_data.get('on_vacation'):
            user_returns_from_vacation(user)

        if not old_instance.on_vacation and serializer.validated_data.get('on_vacation'):
            user_begins_vacation(user)

        if not old_instance.follow_me and serializer.validated_data.get('follow_me'):
            follow_user(user)

        # Since if we have gotten this far, we know that API key is valid, we set it here.
        api_validated = serializer.validated_data.get('api_key', None)
        if api_validated:
            serializer.validated_data['api_valid'] = True

        return serializer


class ContactViewSet(RequestLoggingMixin, generics.CreateAPIView, viewsets.GenericViewSet):
    """
    Endpoint for contacting the developers. POSTing to this endpoint will send us an email.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ContactSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form = UserContactCustomForm(data=serializer.data, request=self.request)

        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        form.save()

        return Response(status=status.HTTP_202_ACCEPTED)


