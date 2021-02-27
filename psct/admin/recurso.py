from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from psct.admin.base import EditalPSCTAdmin
from psct.forms import recurso as forms
from psct.models import recurso as models


class ParecerAvaliador(CompareVersionAdmin):
    list_display = (
        "candidato",
        "avaliador_display",
        "aceito_display",
        "concluido_display",
    )
    search_fields = (
        "avaliador__first_name",
        "avaliador__last_name",
        "avaliador__username",
        "recurso__inscricao__candidato__nome",
        "recurso__inscricao__candidato__cpf",
    )
    list_filter = (
        "recurso__fase",
        ("recurso__fase__edital", admin.RelatedOnlyFieldListFilter),
        "recurso__inscricao__curso__campus",
        ("recurso__inscricao__curso", admin.RelatedOnlyFieldListFilter),
    )
    form = forms.ParecerAvaliadorAdminForm

    def aceito_display(self, obj):
        return obj.get_aceito_display()

    aceito_display.short_description = "Aceito"

    def concluido_display(self, obj):
        return obj.get_concluido_display()

    concluido_display.short_description = "Concluído"

    def avaliador_display(self, obj):
        return f"{obj.avaliador.get_full_name()} ({obj.avaliador})"

    avaliador_display.short_description = "Avaliador"

    def candidato(self, obj):
        return obj.recurso.inscricao.candidato

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.ParecerAvaliador, ParecerAvaliador)
admin.site.register(models.FaseRecurso, EditalPSCTAdmin)
