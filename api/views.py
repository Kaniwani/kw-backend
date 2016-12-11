from rest_framework import permissions

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
