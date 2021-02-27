from ajax_select import fields as ajax_fields

from base.custom.filters import Filter
from psct.models import FaseAjustePontuacao


class AvaliadorFilter(Filter):
    parameter_name = "avaliador"
    title = "Avaliador"

    def get_choices(self, queryset):
        return []

    def get_queryset(self, queryset):
        value = self.get_value()
        if value:
            return queryset.filter(
                mailbox_pontuacao_avaliador__avaliador__username=value
            ).distinct()
        return queryset

    def get_form_field(self, queryset):
        return ajax_fields.AutoCompleteSelectField(
            "servidores", required=False, help_text="", label=self.title
        )


class HomologadorFilter(AvaliadorFilter):
    parameter_name = "homologador"
    title = "Homologador"

    def get_queryset(self, queryset):
        value = self.get_value()
        if value:
            return queryset.filter(
                mailbox_pontuacao_homologador__homologador__username=value
            ).distinct()
        return queryset


class FaseAjustePontuacaoFilter(Filter):
    parameter_name = "fase_ajuste_pontuacao"
    title = "Fase de Ajuste de Pontuação"

    def get_choices(self, queryset):
        return [("", "---------")] + [
            (f.id, str(f)) for f in FaseAjustePontuacao.objects.all()
        ]

    def get_queryset(self, queryset):
        value = self.get_value()
        if value:
            return queryset.filter(pilhainscricaoajuste__fase=value).distinct()
        return queryset


class IndeferimentoEspecialFilter(Filter):
    parameter_name = "indeferimento_especial"
    title = "Indeferimento Especial"

    def get_choices(self, queryset):
        return [("", "---------"), ("SIM", "Sim"), ("NAO", "Não")]

    def get_queryset(self, queryset):
        value = self.get_value()
        if value:
            if value == "SIM":
                return queryset.filter(indeferimento_especial__isnull=False).distinct()
            elif value == "NAO":
                return queryset.filter(indeferimento_especial__isnull=True).distinct()
        return queryset
