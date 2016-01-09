from django.conf.urls import patterns, url
from kw_webapp.views import Logout, Review, Register, RecordAnswer, Dashboard, ReviewSummary, UnlockLevels, \
    UnlockRequested, ForceSRSCheck, About, \
    Settings, LevelVocab, ToggleVocabLockStatus, LockRequested, UnlockAll, Error404
from kw_webapp.forms import UserLoginForm

urlpatterns = patterns('',
                       url(r'^$', Dashboard.as_view(), name="home"),
                       url(r'^login/$', 'django.contrib.auth.views.login',
                           {'template_name': 'registration/login.html',
                            'authentication_form': UserLoginForm},
                           name="login"),
                       url(r'^register/$', Register.as_view(), name="register"),
                       url(r'^logout/$', Logout.as_view(), name="logout"),
                       url(r'^review/$', Review.as_view(), name="review"),
                       url(r'^summary/$', ReviewSummary.as_view(), name="summary"),
                       url(r'^record_answer/$', RecordAnswer.as_view(), name="record_answer"),
                       url(r'^vocabulary/$', UnlockLevels.as_view(), name="vocab"),
                       url(r'^levelunlock/$', UnlockRequested.as_view(), name="do_unlock"),
                       url(r'^levellock/$', LockRequested.as_view(), name="do_lock"),
                       url(r'^unlockall/', UnlockAll.as_view(), name="unlock_all"),
                       url(r'^force_srs/$', ForceSRSCheck.as_view(), name="force_srs"),
                       url(r'^about/$', About.as_view(), name='about'),
                       url(r'^vocabulary/(?P<level>\d{1,2})/$', LevelVocab.as_view(), name='vocab_level'),
                       url(r'^togglevocab/$', ToggleVocabLockStatus.as_view(), name='toggle_vocab_lock'),
                       url(r'^settings/$', Settings.as_view(), name='settings'),
                       url(r'^404/$', Error404.as_view(), name='fourohfour')
                       )
