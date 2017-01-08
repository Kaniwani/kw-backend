from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as authviews

from api import views
from api.views import ReviewViewSet, VocabularyViewSet, ReadingViewSet, LevelViewSet, SynonymViewSet, \
    FrequentlyAskedQuestionViewSet, AnnouncementViewSet

router = DefaultRouter()
router.register(r'review', ReviewViewSet, base_name="review")
router.register(r'vocabulary', VocabularyViewSet, base_name="vocabulary")
router.register(r'reading', ReadingViewSet, base_name="reading")
router.register(r'level', LevelViewSet, base_name="level")
router.register(r'synonym', SynonymViewSet, base_name="synonym")
router.register(r'faq', FrequentlyAskedQuestionViewSet, base_name='faq')
router.register(r'announcement', AnnouncementViewSet, base_name='announcement')

urlpatterns = router.urls + [

    url(r'^profiles/$', views.ProfileList.as_view()),
    url(r'^profiles/(?P<pk>[0-9]+)$', views.ProfileDetail.as_view()),


    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^token-auth/', authviews.obtain_auth_token)
]

