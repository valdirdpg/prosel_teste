from django import forms
from django.contrib.admin.widgets import AdminDateWidget

from editais.choices import CronogramaChoices, EditalChoices
from editais.models import Edital, PeriodoSelecao


class PeriodoSelecaoInlineForm(forms.ModelForm):
    tipo = forms.TypedChoiceField(
        choices=CronogramaChoices.choices(), initial="SELECAO", disabled=True
    )

    class Meta:
        model = PeriodoSelecao
        exclude = ()


class EditalForm(forms.ModelForm):
    inscricao_inicio = forms.DateField(
        label="Início", required=True, widget=AdminDateWidget()
    )
    inscricao_fim = forms.DateField(
        label="Fim", required=True, widget=AdminDateWidget()
    )

    class Meta:
        model = Edital
        exclude = ()
        widgets = {"tipo": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance", None)
        initial = kwargs.get("initial", {})
        if instance:
            periodo = PeriodoSelecao.objects.filter(
                inscricao=True, edital=instance.id
            ).first()
            if periodo:
                initial.update(
                    {"inscricao_inicio": periodo.inicio, "inscricao_fim": periodo.fim}
                )
        else:
            initial.update({"tipo": EditalChoices.ABERTURA.name})
        kwargs.update({"initial": initial})
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        params = {
            "numero": cleaned_data.get("numero"),
            "ano": cleaned_data.get("ano"),
            "setor_responsavel": cleaned_data.get("setor_responsavel"),
        }

        qs = Edital.objects.filter(**params)
        if self.instance:
            qs = qs.exclude(pk=self.instance.id)
        if qs.exists():
            raise forms.ValidationError(
                "Já existe um edital cadastrado com o mesmo número e ano pertencente a este setor."
            )
        return self.cleaned_data