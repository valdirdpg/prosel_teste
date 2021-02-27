from django import forms

from base.forms import Form
from cursos.models import Campus
from editais.models import Edital
from psct.models.inscricao import ProcessoInscricao


class DemandaForm(Form):
    FORMACAO_CHOICES = (
        ("", "Todas as Modalidades"),
        ("INTEGRADO", "Integrado"),
        ("SUBSEQUENTE", "Subsequente"),
    )
    formacao = forms.ChoiceField(
        label="Formação", choices=FORMACAO_CHOICES, required=False
    )
    campus = forms.ModelChoiceField(
        label="Campus",
        empty_label="Todos",
        required=False,
        queryset=Campus.objects.all(),
    )
    processo_inscricao = forms.ModelChoiceField(
        label="Processo Seletivo",
        empty_label="Todos",
        required=False,
        queryset=ProcessoInscricao.objects.all(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["campus"].queryset = self.fields["campus"].queryset.filter(
            id__in=ProcessoInscricao.objects.all().values_list("cursos__campus__id")
        )


class EditalForm(Form):
    edital = forms.ModelChoiceField(
        label="Edital",
        empty_label="Todos",
        required=False,
        queryset=Edital.objects.filter(processo_inscricao__isnull=False),
    )
