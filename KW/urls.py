from django.conf.urls import patterns, include, url

from django.contrib import admin
from rest_framework import routers

import kw_webapp
from kw_webapp.forms import UserLoginForm
from kw_webapp.views import Logout
from kw_webapp.views import Register

admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'user', kw_webapp.views.UserViewSet)
router.register(r'review', kw_webapp.views.ReviewViewSet)
router.register(r'profile', kw_webapp.views.ProfileViewSet)

urlpatterns = patterns('',
                       url(r'^$', 'kw_webapp.views.home', name='home'),


                       url(r'^auth/login/$', 'django.contrib.auth.views.login',
                           {'template_name': 'registration/login.html',
                            'authentication_form': UserLoginForm},
                           name="login"),
                       url(r'^auth/register/$', Register.as_view(), name="register"),
                       url(r'^auth/logout/$', Logout.as_view(), name="logout"),
                       url(r'^auth/password_reset/$', 'django.contrib.auth.views.password_reset',
                           name="password_reset",
                           kwargs={"template_name": "registration/password_reset_form.html"}),

                       url(r'^auth/password_reset/sent/$', 'django.contrib.auth.views.password_reset_done',
                           name="password_reset_done",
                           kwargs={"template_name": "registration/password_reset_done.html"}),

                       url(r'auth/password_reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
                           'django.contrib.auth.views.password_reset_confirm', name='password_reset_confirm'),
                       url(r'^auth/password_reset/complete/$', 'django.contrib.auth.views.password_reset_complete', name="password_reset_complete"),
                       url(r'^api/', include(router.urls)),
                       url(r'^kw/', include('kw_webapp.urls', namespace='kw')),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^contact/', include('contact_form.urls', namespace='contact')),
                       url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
                       )
