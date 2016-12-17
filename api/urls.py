from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as authviews

from api import views
from api.views import ReviewViewSet

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, base_name="review")
urlpatterns = router.urls + [

    url(r'^profiles/$', views.ProfileList.as_view()),
    url(r'^profiles/(?P<pk>[0-9]+)$', views.ProfileDetail.as_view()),

    url(r'^vocabulary/$', views.VocabularyList.as_view()),
    url(r'^vocabulary/(?P<pk>[0-9]+)$', views.VocabularyDetail.as_view()),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^token-auth/', authviews.obtain_auth_token)
]

