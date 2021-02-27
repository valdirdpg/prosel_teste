from django import forms
from django.conf import settings
from django.contrib.auth.forms import (
    PasswordResetForm,
    SetPasswordForm,
    AuthenticationForm,
)
from django.utils.translation import ugettext_lazy as _
from snowpenguin.django.recaptcha2.widgets import (
    ReCaptchaWidget,
)  # pylint: disable=import-error
from base.fields import SafeReCaptchaField
from psct.validators import senha_eh_valida
from base.forms import Form


class BSPasswordResetForm(PasswordResetForm):  # BS == Bootstrap
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].label = _("Email address")
        self.fields["email"].widget.attrs.update({"class": "form-control"})


class BSSetPasswordForm(SetPasswordForm, Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].validators.append(senha_eh_valida)
        self.fields["new_password2"].validators.append(senha_eh_valida)
        self.fields[
            "new_password1"
        ].help_text = "A senha deve conter letras, números e, no mínimo, 8 caracteres."
        self.fields["new_password2"].help_text = self.fields["new_password1"].help_text


class CandidatoAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="CPF",
        max_length=15,
        help_text="Apenas números (não é necessário '.' ou '-')",
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput,
        help_text='<a href="/password_reset/" class="pull-right">Criar ou recuperar senha</a>',
    )
    if not settings.DEBUG:
        captcha = SafeReCaptchaField(widget=ReCaptchaWidget())
