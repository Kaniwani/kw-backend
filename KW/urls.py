from django.conf.urls import patterns, include, url

from django.contrib import admin
from rest_framework import routers

import kw_webapp

admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'user', kw_webapp.views.UserViewSet)
router.register(r'review', kw_webapp.views.ReviewViewSet)
router.register(r'profile', kw_webapp.views.ProfileViewSet)

urlpatterns = patterns('',
                       url(r'^$', 'kw_webapp.views.home', name='home'),
                       url(r'^api/', include(router.urls)),
                       url(r'^kw/', include('kw_webapp.urls', namespace="kw")),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^contact/', include('contact_form.urls', namespace='contact')),
                       url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
                       )
