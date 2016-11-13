from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions

from api.serializers import ProfileSerializer, ReviewSerializer
from kw_webapp.models import Profile

from rest_framework import mixins
from rest_framework import generics
from kw_webapp.tasks import get_users_current_reviews


class ReviewList(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return get_users_current_reviews(self.request.user)


class ProfileList(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer


class ProfileListNew(generics.ListCreateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

class ProfileDetail(generics.RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer


