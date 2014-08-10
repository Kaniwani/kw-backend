from django.conf.urls import patterns, include, url

from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'kw_webapp.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^kw/', include('kw_webapp.urls', namespace="kw")),
    url(r'^admin/', include(admin.site.urls)),
)
