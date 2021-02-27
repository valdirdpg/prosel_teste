from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from psct.admin.reversion import CompareVersionAdmin, PermissionCompareVersionAdmin
from psct.forms import inscricao as forms
from psct.models import inscricao as models


class ModalidadeAdmin(CompareVersionAdmin):
    fields = ("equivalente", "texto")
    ordering = ("texto",)

class ProcessoInscricaoAdmin(CompareVersionAdmin):
    list_filter = (
        ("edital", admin.RelatedOnlyFieldListFilter),
        "data_inicio",
        "data_encerramento",
    )
    autocomplete_fields = ("edital",)
    list_display = ("edital", "data_inicio", "data_encerramento", "acoes")
    filter_vertical = ("cursos",)
    form = forms.ProcessoInscricaoForm

    def has_delete_permission(self, request, obj=None):
        return False

    @mark_safe
    def acoes(self, obj):
        return '<a class="btn btn-sm btn-default" href="{}"> Adicionar vagas</a>'.format(
            reverse("adicionar_curso_edital_psct", kwargs=dict(pk=obj.pk))
        )

    acoes.short_description = "Ação"


class InscricaoConcluidaFilter(admin.SimpleListFilter):

    title = "Inscrição concluída"
    parameter_name = "inscricao_concluida"

    def lookups(self, request, model_admin):
        return [(0, "Não"), (1, "Sim")]

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.filter(aceite=bool(int(value)))
        return queryset


class InscricaoAdmin(PermissionCompareVersionAdmin):
    list_filter = (
        ("edital", admin.RelatedOnlyFieldListFilter),
        ("curso", admin.RelatedOnlyFieldListFilter),
        "curso__campus",
        "modalidade_cota",
        InscricaoConcluidaFilter,
    )
    list_display = (
        "candidato",
        "curso",
        "concluida",
        "visualizar",
        "modalidade_cota",
        "auditoria",
    )
    # list_display_links = None
    search_fields = (
        "candidato__nome",
        "candidato__cpf",
        "candidato__email",
        "candidato__user__username",
    )

    compare_exclude = ["resultados_preliminares"]
    form = forms.InscricaoFormAutocomplete

    def get_list_display_links(self, request, list_display):
        if request.user.is_superuser:
            return super().get_list_display_links(request, list_display)
        return None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if obj:
            return request.user.is_superuser
        return request.user.has_perm("psct.list_inscricao") or request.user.has_perm(
            "psct.change_inscricao"
        )

    @mark_safe
    def visualizar(self, obj):
        if obj.aceite:
            return f'<a href="{obj.get_absolute_url()}">Visualizar</a>'
        return "Indisponível"

    visualizar.short_description = "Ver inscrição"

    @mark_safe
    def auditoria(self, obj):
        return '<a href="{}">Visualizar</a>'.format(
            reverse("inscricao_history_psct", kwargs=dict(pk=obj.pk))
        )

    auditoria.short_description = "Auditoria"

    def concluida(self, obj):
        if obj.aceite:
            return "Sim"
        return "Não"

    concluida.short_description = "Concluída"


class ModalidadeVagaCursoEditalAdmin(CompareVersionAdmin):
    list_display = ("get_edital", "get_curso", "modalidade", "quantidade_vagas")
    fields = ("curso_edital", "modalidade", "quantidade_vagas")

    def get_edital(self, obj):
        return obj.curso_edital.edital

    get_edital.short_description = "Edital"

    def get_curso(self, obj):
        return obj.curso_edital.curso

    get_curso.short_description = "Curso"


class ModalidadeVagaCursoEditalInline(admin.TabularInline):
    model = models.ModalidadeVagaCursoEdital
    ordering = ("modalidade",)
    fields = ("modalidade", "quantidade_vagas", "multiplicador")
    extra = 0
    formset = forms.ModalidadeVagaInlineFormSet

    def get_max_num(self, request, obj=None, **kwargs):
        return models.Modalidade.objects.count()

    def get_min_num(self, request, obj=None, **kwargs):
        return models.Modalidade.objects.count()


class CursoEditalAdmin(CompareVersionAdmin):
    readonly_fields = ("get_quantidade_vagas_total",)
    fields = ("edital", "curso", "get_quantidade_vagas_total")
    list_display = (
        "curso",
        "get_quantidade_vagas_total",
        "get_quantidade_modalidades_cadastradas",
        "edital",
    )
    list_filter = (
        "curso__modalidade",
        "curso__campus",
        "curso__turno",
        ("edital", admin.RelatedOnlyFieldListFilter),
        ("curso", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        "curso__curso__nome",
        "curso__modalidade",
        "curso__campus__nome",
        "curso__turno",
    )
    form = forms.CursoEditalForm
    inlines = [ModalidadeVagaCursoEditalInline]

    def get_quantidade_vagas_total(self, obj):
        vagas = obj.qtd_vagas_total
        return vagas if vagas else 0

    get_quantidade_vagas_total.short_description = "Vagas"

    def get_quantidade_modalidades_cadastradas(self, obj):
        total_modalidades = models.ModalidadeVagaCursoEdital.objects.filter(
            curso_edital=obj
        ).count()
        return total_modalidades if total_modalidades else 0

    get_quantidade_modalidades_cadastradas.short_description = "Modalidades preenchidas"

    def has_add_permission(self, request):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ("get_quantidade_vagas_total",)
        return "edital", "curso", "get_quantidade_vagas_total"


admin.site.register(models.Modalidade, ModalidadeAdmin)
admin.site.register(models.ProcessoInscricao, ProcessoInscricaoAdmin)
admin.site.register(models.Inscricao, InscricaoAdmin)
admin.site.register(models.CursoEdital, CursoEditalAdmin)
