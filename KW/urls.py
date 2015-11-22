from django.conf.urls import patterns, include, url

from django.contrib import admin
#from kw_webapp.models import Announcement
from rest_framework import routers

import kw_webapp

admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'users', kw_webapp.views.UserViewSet)
router.register(r'groups', kw_webapp.views.GroupViewSet)
router.register(r'reviews', kw_webapp.views.ReviewViewSet)


urlpatterns = patterns('',
                       url(r'^$', 'kw_webapp.views.home', name='home'),
                       url(r'^api/', include(router.urls)),
                       url(r'^kw/', include('kw_webapp.urls', namespace="kw")),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
                       )
