from django.conf.urls import url, include
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_jwt import views as jwtviews
from api.views import (
    ReviewViewSet,
    VocabularyViewSet,
    ReadingViewSet,
    LevelViewSet,
    ReadingSynonymViewSet,
    FrequentlyAskedQuestionViewSet,
    AnnouncementViewSet,
    UserViewSet,
    ContactViewSet,
    ProfileViewSet,
    ReportViewSet,
    MeaningSynonymViewSet,
)

router = DefaultRouter()
router.register(r"review", ReviewViewSet, basename="review")
router.register(r"profile", ProfileViewSet, basename="profile")
router.register(r"vocabulary", VocabularyViewSet, basename="vocabulary")
router.register(r"report", ReportViewSet, basename="report")
router.register(r"reading", ReadingViewSet, basename="reading")
router.register(r"level", LevelViewSet, basename="level")
router.register(
    r"synonym/reading", ReadingSynonymViewSet, basename="reading-synonym"
)
router.register(
    r"synonym/meaning", MeaningSynonymViewSet, basename="meaning-synonym"
)
router.register(r"faq", FrequentlyAskedQuestionViewSet, basename="faq")
router.register(r"announcement", AnnouncementViewSet, basename="announcement")
router.register(r"user", UserViewSet, basename="user")
router.register(r"contact", ContactViewSet, basename="contact")

app_name = "api"

urlpatterns = router.urls + [
    path(r"auth/login/", jwtviews.obtain_jwt_token),
    path(r"auth/", include(("djoser.urls.base", "auth"), namespace="auth")),
]
