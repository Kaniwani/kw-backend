from django.http import HttpResponseForbidden
from django.utils import timezone
from rest_framework import mixins
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.views import APIView

from api.permissions import IsAdminOrReadOnly
from api.serializers import ProfileSerializer, ReviewSerializer, VocabularySerializer, StubbedReviewSerializer, \
    HyperlinkedVocabularySerializer, ReadingSerializer, LevelSerializer, SynonymSerializer, \
    FrequentlyAskedQuestionSerializer
from api.filters import VocabularyFilter, ReviewFilter
from kw_webapp import constants
from kw_webapp.models import Profile, Vocabulary, UserSpecific, Reading, Level, AnswerSynonym, FrequentlyAskedQuestion

from rest_framework import generics
from kw_webapp.tasks import get_users_current_reviews, unlock_eligible_vocab_from_levels, lock_level_for_user


class ListRetrieveUpdateViewSet(mixins.ListModelMixin,
                                mixins.UpdateModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    """
    A viewset that provides `List`, `Update`, and `Retrieve` actions.
    Must override: .queryset, .serializer_class
    """
    pass


class ReadingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Reading.objects.all()
    serializer_class = ReadingSerializer


class SynonymViewSet(viewsets.ModelViewSet):
    serializer_class = SynonymSerializer

    def get_queryset(self):
        return AnswerSynonym.objects.filter(review__user=self.request.user)


class LevelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Level.objects.all()

    def list(self, request, *args, **kwargs):
        level_dicts = []
        for level in range(constants.LEVEL_MIN, constants.LEVEL_MAX + 1):
            pre_serialized_dict = {'level': level,
                                   'unlocked': True if level in request.user.profile.unlocked_levels_list() else False,
                                   'vocabulary_count': Vocabulary.objects.filter(readings__level=level).count()}
            if level <= request.user.profile.level:
                pre_serialized_dict['lock_url'] = self._build_lock_url(level)
                pre_serialized_dict['unlock_url'] = self._build_unlock_url(level)
            level_dicts.append(pre_serialized_dict)

        serializer = LevelSerializer(level_dicts, many=True)
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

        limit = None
        if 'count' in request.query_params:
            limit = int(request.query_params['count'])

        unlocked_this_request, total_unlocked, locked = unlock_eligible_vocab_from_levels(user, requested_level, limit)
        level, created = user.profile.unlocked_levels.get_or_create(level=requested_level)
        fully_unlocked = True if limit is None else False

        # If user has repeatedly done partial unlocks, eventually they will fully unlock the level.
        if limit and unlocked_this_request == limit:
            level.partial = True
            level.save()
        elif limit and unlocked_this_request < limit:
            level.partial = False
            fully_unlocked = True
            level.save()

        return Response(dict(unlocked_now=unlocked_this_request,
                             total_unlocked=total_unlocked,
                             locked=locked,
                             fully_unlocked=fully_unlocked))

    @detail_route(methods=['POST'])
    def lock(self, request, pk=None):
        requested_level = pk
        if request.user.profile.level == int(requested_level):
            request.user.profile.follow_me = False
            request.user.profile.save()
        removed_count = lock_level_for_user(requested_level, request.user)

        return Response({"locked": removed_count})


class VocabularyViewSet(viewsets.ReadOnlyModelViewSet):
    filter_class = VocabularyFilter
    queryset = Vocabulary.objects.all()

    def get_serializer_class(self):
        if self.request.query_params.get('hyperlink', 'false') == 'true':
            return HyperlinkedVocabularySerializer
        else:
            return VocabularySerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    filter_class = ReviewFilter

    @list_route(methods=['GET'])
    def current(self, request):
        reviews = get_users_current_reviews(request.user)
        page = self.paginate_queryset(reviews)

        if page is not None:
            serializer = StubbedReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = StubbedReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @detail_route(methods=['POST'])
    def correct(self, request, pk=None):
        review = get_object_or_404(UserSpecific, pk=pk)
        if not review.can_be_managed_by(request.user) or not review.needs_review:
            return HttpResponseForbidden("You can't modify that object at this time!")

        was_correct_on_first_try = False if request.data['wrong_before'] == 'true' else True
        review.answered_correctly(was_correct_on_first_try)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['POST'])
    def incorrect(self, request, pk=None):
        review = get_object_or_404(UserSpecific, pk=pk)
        if not review.can_be_managed_by(request.user) or not review.needs_review:
            return HttpResponseForbidden("You can't modify that object at this time!")
        review.answered_incorrectly()

        return Response(status=status.HTTP_204_NO_CONTENT)

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
        return UserSpecific.objects.filter(user=self.request.user)


class FrequentlyAskedQuestionViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = FrequentlyAskedQuestionSerializer
    queryset = FrequentlyAskedQuestion.objects.all()


class ProfileList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer


class ProfileDetail(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
