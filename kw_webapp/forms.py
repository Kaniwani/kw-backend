from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
import requests
from kw_webapp.models import Profile
from django.utils.translation import ugettext, ugettext_lazy as _



class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = False
        self.fields['username'].css_class = "False"
        self.fields['username'].widget.attrs['placeholder'] = "Username"
        self.fields['password'].widget.attrs['placeholder'] = "Password"
        self.fields['password'].label = False
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Sign In", css_class='button -submit'))
        self.helper.form_class = 'login-form'
        self.helper.form_method = 'post'
        self.helper.form_action = ''


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True)
    api_key = forms.CharField(required=True, max_length=100)

    def __init__(self, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)

        for field_name in ['username', 'password1', 'password2']:
            self.fields[field_name].help_text = None

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.add_input(Submit("submit", "Submit", css_class='button -submit'))
        self.helper.form_class = 'login-form'
        self.helper.form_style = "default"
        self.helper.help_text_inline = True
        self.helper.error_text_inline = False

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            u = User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        else:
            raise ValidationError("Email is already in use")


    def clean_api_key(self):
        api_key = self.cleaned_data['api_key']
        r = requests.get("https://www.wanikani.com/api/user/{}/user-information".format(api_key))
        if r.status_code == 200:
            json_data = r.json()
            if "error" in json_data.keys():
                raise ValidationError("API Key not associated with a WaniKani User!")
        return api_key

    class Meta:
        model = User
        fields = ("username", "email")


class SettingsForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['api_key', 'level',  'follow_me', 'auto_advance_on_success', 'auto_expand_answer_on_failure', 'only_review_burned']
        help_texts = {
            "follow_me": ("If you disable this, Kaniwani will no longer automatically unlock things as you unlock them in Wanikani."),
        }
        labels = {
            "follow_me": "Follow Wanikani Progress",
            "auto_advance_on_success": "Automatically advance to next item in review if answer was correct.",
            "auto_expand_answer_on_failure": "Automatically show kanji and kana if you answer incorrectly.",
            "only_review_burned": "Review only items that you have burned in Wanikani."
        }
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.add_input(Submit("submit", "Save", css_class='pure-button pure-button-primary'))
        self.helper.form_class = 'pure-form pure-form-stacked'
        self.helper.label_class = ''
        self.helper.field_class = 'pure-input-1'
        self.helper.form_style = "default"
        self.helper.help_text_inline = False
        self.helper.error_text_inline = False
        super(SettingsForm, self).__init__(*args, **kwargs)
        self.fields['level'].widget.attrs['readonly'] = True

    def clean_api_key(self):
        api_key = self.cleaned_data['api_key']
        r = requests.get("https://www.wanikani.com/api/user/{}/user-information".format(api_key))
        if r.status_code == 200:
            json_data = r.json()
            if "error" in json_data.keys():
                raise ValidationError("API Key not associated with a WaniKani User!")
        print("cleaned api Key...")
        return api_key
