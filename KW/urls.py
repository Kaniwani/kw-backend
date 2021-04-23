from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView, TemplateView
from rest_framework.schemas import get_schema_view

from KW import settings

admin.autodiscover()

urlpatterns = (
    url(r"^$", RedirectView.as_view(url="/redoc/")),
    url(r"^openapi/", get_schema_view(title="Kaniwani",description="Kaniwani API Documentation"), name="openapi-schema"),
    url(r'redoc/', TemplateView.as_view(
        template_name="kw_webapp/redoc.html",
        extra_context={"schema_url": "openapi-schema"}
    ), name="redoc"),
    url(r"^admin/", admin.site.urls),
    url(r"^api/v1/", include("api.urls", namespace="api")),
)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += (url(r"^silk/", include("silk.urls", namespace="silk")),)
    urlpatterns += (url(r"^__debug__/", include(debug_toolbar.urls)),)
