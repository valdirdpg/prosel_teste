from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet

from base.forms import Form, ModelForm
from psct.forms.inscricao import BaseNotaForm
from psct.models import pontuacao as models

WIDGETS_PONTUACAO = {
    "inscricao": forms.HiddenInput,
    "inscricao_preanalise": forms.HiddenInput,
    "fase": forms.HiddenInput,
    "valor": forms.HiddenInput,
    "valor_pt": forms.HiddenInput,
    "valor_mt": forms.HiddenInput,
}


class PontuacaoAvaliadorForm(ModelForm):
    class Meta:
        exclude = []
        model = models.PontuacaoAvaliador
        widgets = WIDGETS_PONTUACAO.copy()
        widgets["avaliador"] = forms.HiddenInput


class PontuacaoHomologadorForm(ModelForm):
    SITUACAO_CHOICES = [
        ("", "---------"),
        (
            "DEFERIR",
            'Alterar a situação da inscrição para "DEFERIDA" e atualizar suas notas.',
        ),
        ("INDEFERIR", "Manter a inscrição como indeferida."),
    ]
    situacao = forms.ChoiceField(label="Situação", choices=SITUACAO_CHOICES)

    class Meta:
        exclude = []
        model = models.PontuacaoHomologador
        widgets = WIDGETS_PONTUACAO.copy()
        widgets["homologador"] = forms.HiddenInput


class NotaForm(BaseNotaForm):
    def __init__(self, pontuacao_form, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pontuacao_form = pontuacao_form

    def clean(self):
        super().clean()
        ano = self.cleaned_data.get("ano")
        if self.pontuacao_form and ano:
            if ano not in self.pontuacao_form.get_anos_requeridos():
                raise ValidationError({"ano": "Ano inválido"})
        return self.cleaned_data


class NotasFormSet(BaseInlineFormSet):
    def __init__(self, pontuacao, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pontuacao = pontuacao

    def clean(self):
        super().clean()
        forms = [f for f in self.forms if f.is_valid() and f.cleaned_data]
        forms_valids = len(forms)
        anos_informados = [
            int(f.cleaned_data["ano"]) for f in forms if not f.cleaned_data["DELETE"]
        ]
        if self.pontuacao:
            anos = self.pontuacao.get_anos_requeridos()
            if sorted(anos) != sorted(anos_informados):
                if anos == [0]:
                    anos = "Supletivo/Enem/Outros"
                raise ValidationError(
                    "Você não informou a nota de todos os anos. Os anos exigidos são: {}.".format(
                        anos
                    )
                )
        if forms_valids - len(self.deleted_forms) < 1:
            raise ValidationError("Você não pode remover todas as notas.")

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["pontuacao_form"] = self.pontuacao
        return kwargs


class ImportarForm(Form):
    justificativa = forms.ModelChoiceField(
        label="Justificativa de indeferimento",
        queryset=models.analise_models.JustificativaIndeferimento.objects.all(),
    )

    def __init__(self, fase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[
            "justificativa"
        ].queryset = fase.edital.justificativaindeferimento_set.all()
