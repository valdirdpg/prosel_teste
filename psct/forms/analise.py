from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from base.forms import Form, ModelForm
from psct.models import analise as models
from psct.models.consulta import Coluna


class CriterioExclusaoForm(Form):
    criterio = forms.ModelChoiceField(
        label="Critério Utilizado para Excluir Avaliadores/Homologadores",
        queryset=Coluna.objects.filter(
            entidade__app_label="psct", entidade__model="inscricaopreanalise"
        ),
    )


class GrupoExclusaoForm(Form):
    def __init__(self, fase, coluna, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fase = fase
        self.coluna = coluna
        valores = (
            models.InscricaoPreAnalise.objects.filter(fase=fase)
            .values_list(coluna.query_string, flat=True)
            .distinct()
        )
        for valor in valores:
            field = f"field_{valor}"
            label = coluna.get_format()(valor)
            self.fields[field] = forms.ModelChoiceField(
                queryset=self.get_grupos(fase.edital), label=label, required=False
            )
            self.fields[field].widget.attrs["class"] = "form-control"
        self.get_initial()

    def get_grupos(self, edital):
        return Group.objects.filter(
            grupos_editais__isnull=False, grupos_editais__edital=edital
        ).distinct()

    def get_choices(self, fase):
        return [(g.id, g) for g in self.get_grupos(fase.edital)]

    def save(self):
        for field in self.fields:

            if not self.cleaned_data[field]:
                continue

            valor = field[len("field_") :]
            models.RegraExclusaoGrupo.objects.update_or_create(
                fase=self.fase,
                coluna=self.coluna,
                valor=valor,
                defaults=dict(grupo=self.cleaned_data[field]),
            )

    def get_initial(self):
        for r in models.RegraExclusaoGrupo.objects.filter(
            fase=self.fase, coluna=self.coluna
        ):
            self.fields["field_" + r.valor].initial = r.grupo


class AvaliarInscricaoAvaliadorForm(ModelForm):
    class Meta:
        model = models.AvaliacaoAvaliador
        exclude = []
        widgets = {"inscricao": forms.HiddenInput, "avaliador": forms.HiddenInput}

    def __init__(self, inscricao, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = self.fields["texto_indeferimento"].queryset
        self.fields["texto_indeferimento"].queryset = qs.filter(
            edital=inscricao.fase.edital
        )

    def clean_texto_indeferimento(self):
        situacao = self.cleaned_data.get("situacao")
        texto = self.cleaned_data.get("texto_indeferimento")
        if (
            situacao
            and situacao == models.SituacaoAvaliacao.INDEFERIDA.name
            and not texto
        ):
            raise ValidationError("Você precisa justificar o indeferimento")
        if situacao and situacao == models.SituacaoAvaliacao.DEFERIDA.name and texto:
            raise ValidationError("Inscrição deferida não requer justificativa")
        return texto


class AvaliarInscricaoHomologadorForm(AvaliarInscricaoAvaliadorForm):
    class Meta:
        model = models.AvaliacaoHomologador
        exclude = []
        widgets = {"inscricao": forms.HiddenInput, "homologador": forms.HiddenInput}


class AvaliacaoAvaliadorAdminForm(ModelForm):
    class Meta:
        model = models.AvaliacaoAvaliador
        fields = ["concluida"]

    def clean(self):
        inscricao = self.instance.inscricao
        if inscricao and inscricao.avaliacao:
            raise ValidationError(
                "Você não pode alterar a avaliação pois o homologador já avaliou a inscrição"
            )
