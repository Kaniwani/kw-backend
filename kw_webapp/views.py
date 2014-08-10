from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import TemplateView, ListView, DetailView, FormView, CreateView
from kw_webapp.models import Profile, Vocabulary
from kw_webapp.forms import UserCreateForm


# Create your views here.

class Home(TemplateView):
    template_name = "kw_webapp/home.html"


class Review(ListView):
    template_name = "kw_webapp/review.html"
    model = Vocabulary

    def get_queryset(self):
        user = self.request.user
        return Vocabulary.objects.filter(reading__level__lte=user.profile.level)

class Logout(TemplateView):
    def get(self, request, *args, **kwargs):
        logout(request=request)
        return HttpResponseRedirect(reverse_lazy("kw:home"))


class Register(FormView):
    template_name = "registration/registration.html"
    form_class = UserCreateForm
    success_url = reverse_lazy("kw:home")

    def form_valid(self, form):
        user = form.save()
        profile = Profile.objects.create(user=user, api_key=form.cleaned_data['api_key'], level=1)
        return HttpResponseRedirect(reverse_lazy("kw:home"))


def home(request):
    return HttpResponseRedirect(reverse_lazy('kw:home'))


