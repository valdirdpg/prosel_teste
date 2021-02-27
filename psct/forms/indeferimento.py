from django import forms

from base.forms import ModelForm
from psct.models import indeferimento as models


class IndeferimentoEspecialForm(ModelForm):
    class Meta:
        model = models.IndeferimentoEspecial
        exclude = []
        widgets = {
            "inscricao": forms.HiddenInput,
            "autor": forms.HiddenInput,
            "fase": forms.HiddenInput,
        }

    def __init__(self, inscricao, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = self.fields["motivo_indeferimento"].queryset
        self.fields["motivo_indeferimento"].queryset = qs.filter(
            edital=inscricao.fase.edital
        )
