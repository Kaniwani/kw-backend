from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns

from api import views

urlpatterns = [
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^profiles/$', views.ProfileList.as_view()),
    url(r'^profiles/(?P<pk>[0-9]+)$', views.ProfileDetail.as_view()),

    url(r'^reviews/$', views.ReviewList.as_view())
   # url(r'^reviews/(?P<pk>[0-9]+)$', views.ReviewDetail.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)