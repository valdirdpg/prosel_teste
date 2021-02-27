from base.custom.filters import FieldFilter, Filter
from psct.models.analise import Edital, InscricaoPreAnalise


class FormacaoFilter(Filter):
    parameter_name = "formacao"
    title = "Formação"

    def get_choices(self, queryset):
        return [
            ("", "-------"),
            ("INTEGRADO", "Integrado"),
            ("SUBSEQUENTE", "Subsequente"),
        ]

    def get_queryset(self, queryset):
        value = self.get_value()
        if value:
            return queryset.filter(curso__formacao=value)
        return queryset


class EditalPSCTFilter(FieldFilter):
    model = InscricaoPreAnalise
    field_path = "fase__edital"

    def __init__(self, request):
        super().__init__(self.model, self.field_path, request)

    def get_choices(self, queryset):
        dash = [("", "--------")]
        qs = Edital.objects.filter(processo_inscricao__isnull=False).distinct()
        choices = [(e.id, e) for e in qs]
        return dash + choices
