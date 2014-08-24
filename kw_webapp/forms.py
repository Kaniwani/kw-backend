from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
import requests


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Login"))
        self.helper.form_class = 'form-horizontal'
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
        self.helper.add_input(Submit("submit", "Submit"))
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
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