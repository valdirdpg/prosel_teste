from django import forms
from form_utils import forms as forms_utils

from base.forms import FieldStyledMixin


class ConfirmacaoForm(FieldStyledMixin, forms_utils.BetterForm):
    aceite = forms.ChoiceField(
        label="Confirma o envio dos emails?",
        choices=[(0, "Não"), (1, "Sim")],
        widget=forms.RadioSelect,
    )
