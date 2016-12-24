from django.http import HttpResponseForbidden
from django.utils import timezone
from rest_framework import mixins
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.serializers import ProfileSerializer, ReviewSerializer, VocabularySerializer, StubbedReviewSerializer
from api.filters import VocabularyFilter
from kw_webapp.models import Profile, Vocabulary, UserSpecific

from rest_framework import generics
from kw_webapp.tasks import get_users_current_reviews


class ListRetrieveUpdateViewSet(mixins.ListModelMixin,
                                mixins.UpdateModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    """
    A viewset that provides `List`, `Update`, and `Retrieve` actions.
    Must override: .queryset, .serializer_class
    """
    pass


class ReviewViewSet(ListRetrieveUpdateViewSet):
    serializer_class = ReviewSerializer

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


class ReviewDetail(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = UserSpecific.objects.all()
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return UserSpecific.objects.filter(user=self.request.user)


class ProfileList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer


class ProfileDetail(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer


class VocabularyList(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Vocabulary.objects.all()
    serializer_class = VocabularySerializer
    filter_class = VocabularyFilter


class VocabularyDetail(generics.RetrieveUpdateAPIView):
    queryset = Vocabulary.objects.all()
    serializer_class = VocabularySerializer
