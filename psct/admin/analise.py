from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from reversion_compare.admin import CompareVersionAdmin

from psct.admin.base import EditalPSCTAdmin
from psct.forms import analise as forms
from psct.models import analise as models


class AvaliacaoAvaliadorAdmin(CompareVersionAdmin):
    list_display = (
        "candidato",
        "avaliador_display",
        "situacao_display",
        "concluida_display",
    )

    search_fields = (
        "avaliador__first_name",
        "avaliador__last_name",
        "avaliador__username",
        "inscricao__candidato__nome",
        "inscricao__candidato__cpf",
    )
    list_filter = (
        "inscricao__fase",
        ("inscricao__fase__edital", admin.RelatedOnlyFieldListFilter),
        "inscricao__curso__campus",
        ("inscricao__curso", admin.RelatedOnlyFieldListFilter),
    )
    form = forms.AvaliacaoAvaliadorAdminForm

    def situacao_display(self, obj):
        return obj.get_situacao_display()

    situacao_display.short_description = "Aceito"

    def concluida_display(self, obj):
        return obj.get_concluida_display()

    concluida_display.short_description = "Concluído"

    def avaliador_display(self, obj):
        return f"{obj.avaliador.get_full_name()} ({obj.avaliador})"

    avaliador_display.short_description = "Avaliador"

    def candidato(self, obj):
        return obj.inscricao.candidato

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class JustificativaIndeferimentoAdmin(EditalPSCTAdmin):
    list_display = ("texto", "edital")
    list_filter = (("edital", admin.RelatedOnlyFieldListFilter),)


class FaseAnaliseAdmin(EditalPSCTAdmin):
    list_display = ("nome", "edital_display", "acoes")
    list_filter = (("edital", admin.RelatedOnlyFieldListFilter),)

    @mark_safe
    def acoes(self, obj):
        url = reverse("resultado_preliminar_psct", kwargs=dict(fase_pk=obj.pk))
        return '<a href="{}" class="btn btn-default btn-xs">Gerar resultado preliminar</a>'.format(
            url
        )

    acoes.short_description = "Ações"

    def edital_display(self, obj):
        return f"{obj.edital.numero}/{obj.edital.ano}"

    edital_display.short_description = "Edital"


admin.site.register(models.JustificativaIndeferimento, JustificativaIndeferimentoAdmin)
admin.site.register(models.AvaliacaoAvaliador, AvaliacaoAvaliadorAdmin)
admin.site.register(models.FaseAnalise, FaseAnaliseAdmin)
