from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import TemplateView, ListView, DetailView, FormView, CreateView, View
from kw_webapp.models import Profile, Vocabulary, UserSpecific
from kw_webapp.forms import UserCreateForm
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone


# Create your views here.

class Home(TemplateView):
    template_name = "kw_webapp/home.html"

@csrf_exempt
def RecordAnswer(request):
    if request.method == "POST":
        us_id = request.POST["user_specific_id"]
        user_correct = request.POST["user_correct"]
        us = UserSpecific.objects.get(pk=us_id)
        if user_correct:
            us.correct += 1
            us.streak += 1
            us.needs_review = False
            us.last_studied = timezone.now()
            us.save()
            return HttpResponse("Correct!")
        else:
            us.incorrect += 1
            us.streak -= 1
            if us.streak < 0:
                us.streak = 0
            us.save()
            return HttpResponse("Incorrect!")






class Review(ListView):
    template_name = "kw_webapp/review.html"
    model = UserSpecific

    def get_context_data(self, **kwargs):
        context = super(Review, self).get_context_data()
        user = self.request.user
        #this may end up unnecessary. Not using it at the moment.
        context["json"] = serializers.serialize("json", UserSpecific.objects.filter(user=user, needs_review=True))

        print(context['json'])
        return context

    def get_queryset(self):
        user = self.request.user
        res = UserSpecific.objects.filter(user=user, needs_review=True)
        return res


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


