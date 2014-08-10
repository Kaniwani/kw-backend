from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.forms import ModelForm
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class UserRegisterForm(forms.Form):
    username = forms.CharField(label="Username", max_length=50)
    email = forms.EmailField()
    api_key = forms.CharField(label="WaniKani API Key", max_length=100)
    pass1 = forms.PasswordInput()
    pass2 = forms.PasswordInput()

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

    class Meta:
        model = User
        fields = ( "username", "email" )