import django
from contact_form.views import ContactFormView
from django.conf.urls import include, url

from django.contrib import admin
from django.contrib.auth.views import password_reset, password_reset_done, password_reset_complete, password_reset_confirm
from django.views.generic import TemplateView
from rest_framework import routers

import kw_webapp
from KW import settings
from kw_webapp.forms import UserLoginForm, PasswordResetFormCustom, UserContactCustomForm
from kw_webapp.views import Logout, home
from kw_webapp.views import Register

admin.autodiscover()

urlpatterns = (
    url(r'^$', home, name='home'),

    ##API
    #url(r'^api/v1/', include('api.urls', namespace='api')),
    ##DOCS
    #url(r'^docs/', include('rest_framework_docs.urls')),
   

    ##All Auth Stuff
    url(r'^auth/login/$', django.contrib.auth.views.login,
        {'template_name': 'registration/login.html',
         'authentication_form': UserLoginForm},
        name="login"),
    url(r'^auth/register/$', Register.as_view(), name="register"),
    url(r'^auth/logout/$', Logout.as_view(), name="logout"),
    url(r'^auth/password_reset/$', password_reset,
        name="password_reset",
        kwargs={"template_name": "registration/password_reset_form.html",
                "password_reset_form": PasswordResetFormCustom}),

    url(r'^auth/password_reset/sent/$', password_reset_done,
        name="password_reset_done",
        kwargs={"template_name": "registration/password_reset_done.html"}),
    url(r'^auth/password_reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        password_reset_confirm, name='password_reset_confirm'),
    url(r'^auth/password_reset/complete/$', password_reset_complete,
        name="password_reset_complete"),
    url(r'^admin/', include(admin.site.urls)),

    ##Contact-related views.
    url(r'^contact/$', ContactFormView.as_view(form_class=UserContactCustomForm), name="contact_form"),
    url(r'^contact/sent/$', TemplateView.as_view(template_name="contact_form/contact_form_sent.html"),
        name='contact_form_sent'),

    ##KW SRS Stuff.
    url(r'^kw/', include('kw_webapp.urls', namespace='kw'))
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += (
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
