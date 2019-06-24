from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from rest_framework.documentation import include_docs_urls

from KW import settings

admin.autodiscover()

urlpatterns = (
    url(r"^$", RedirectView.as_view(url="/docs/")),
    url(r"^docs/", include_docs_urls(title="Kaniwani Docs")),
    url(r"^admin/", admin.site.urls),
    url(r"^api/v1/", include("api.urls", namespace="api")),
)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += (url(r"^__debug__/", include(debug_toolbar.urls)),)
