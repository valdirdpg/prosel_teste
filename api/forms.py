from ajax_select.fields import AutoCompleteSelectField
from django.forms import ModelForm
from rest_framework.authtoken.models import Token


class TokenForm(ModelForm):
    user = AutoCompleteSelectField("users")

    class Meta:
        model = Token
        fields = ("user",)
