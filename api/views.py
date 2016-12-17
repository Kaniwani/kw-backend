from django.http import HttpResponseForbidden
from django.utils import timezone
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.serializers import ProfileSerializer, ReviewSerializer, VocabularySerializer, StubbedReviewSerializer
from api.filters import VocabularyFilter
from kw_webapp.models import Profile, Vocabulary, UserSpecific

from rest_framework import generics
from kw_webapp.tasks import get_users_current_reviews


class ReviewList(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = StubbedReviewSerializer

    def get_queryset(self):
        return get_users_current_reviews(self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
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
        if not review.can_be_managed_by(self.request.user) or not review.needs_review:
            return HttpResponseForbidden("You can't modify that object at this time!")

        previously_wrong = True if request.data['wrong_before'] == 'true' else False
        if not previously_wrong:
            review.correct += 1
            review.streak += 1
            if review.streak >= 9:
                review.burned = True

        review.needs_review = False
        review.last_studied = timezone.now()
        review.save()
        review.set_next_review_time()
        return Response({"status": "correct"})

    @detail_route(methods=['POST'])
    def incorrect(self, request, pk=None):
        review = get_object_or_404(UserSpecific, pk=pk)
        if not review.can_be_managed_by(self.request.user) or not review.needs_review:
            return HttpResponseForbidden("You can't modify that object at this time!")

        review.incorrect += 1
        if review.streak == 7:
            review.streak -= 2
        else:
            review.streak -= 1
        if review.streak < 0:
            review.streak = 0
        review.save()
        return Response({"status": "incorrect"})


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
