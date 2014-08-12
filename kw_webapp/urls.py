from django.conf.urls import patterns, url
from kw_webapp.views import Logout, Review, Register, RecordAnswer, Dashboard
from django.contrib.auth.decorators import login_required
from kw_webapp.forms import UserLoginForm

urlpatterns = patterns('',
    url(r'^$', login_required(Dashboard.as_view()), name="dashboard"),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name':'registration/login.html', 'authentication_form':UserLoginForm}, name="login"),
    url(r'^register/$', Register.as_view(), name="register"),
    url(r'^logout/$', login_required(Logout.as_view()), name="logout"),
    url(r'^review/$', login_required(Review.as_view()), name="review"),
    url(r'^record_answer/$', RecordAnswer, name="record_answer")
)

