from django.conf.urls import patterns, include, url

from django.contrib import admin
#from kw_webapp.models import Announcement
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', 'kw_webapp.views.home', name='home'),
                       url(r'^kw/', include('kw_webapp.urls', namespace="kw")),
                       url(r'^admin/', include(admin.site.urls)),
                       )
