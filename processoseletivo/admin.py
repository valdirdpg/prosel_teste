from django import forms as django_forms
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from image_cropping import ImageCroppingMixin
from reversion_compare.admin import CompareVersionAdmin

from cursos.models import Campus, CursoSelecao
from editais.models import PeriodoConvocacao
from processoseletivo import forms
from processoseletivo import listfilters
from processoseletivo import models
from processoseletivo.models import Chamada, ModalidadeEnum
from psct.admin.reversion import PermissionCompareVersionAdmin


class EdicaoAdmin(admin.ModelAdmin):
    list_display = ("processo_seletivo", "ano", "semestre", "nome")
    ordering = ("processo_seletivo", "-ano", "-semestre", "nome")
    exclude = ("importado",)
    list_filter = ("processo_seletivo", "ano", "semestre")

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.importado:
            return ("arquivo_resultado_csv", "arquivo_lista_espera_csv")
        return []

    class Media:
        css = {"all": ("ps/css/style_admin.css",)}


class EdicaoInline(admin.StackedInline):
    model = models.Edicao
    max_num = 1


class ProcessoSeletivoAdmin(ImageCroppingMixin, admin.ModelAdmin):
    inlines = [EdicaoInline]


class PeriodoConvocacaoInline(admin.TabularInline):
    model = PeriodoConvocacao
    min_num = 3
    extra = 0
    form = forms.PeriodoConvocacaoInlineForm
    formset = forms.PeriodoConvocacaoInlineFormSet


class CampusEtapaListFilter(admin.RelatedOnlyFieldListFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_value_display = "Sistêmico"


class EtapaAdmin(CompareVersionAdmin):
    list_display = ("edicao", "numero", "campus")
    ordering = (
        "-edicao__ano",
        "-edicao__semestre",
        "edicao__nome",
        "-numero",
        "campus",
    )
    list_filter = (
        listfilters.EtapaEdicaoListFilter,
        listfilters.EtapaNumeroListFilter,
        listfilters.EtapaCampusListFilter,
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("edicao", "numero"),
                    ("campus",),
                    ("multiplicador",),
                    ("publica",),
                )
            },
        ),
    )

    inlines = [PeriodoConvocacaoInline]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return "edicao", "multiplicador", "numero", "campus"
        return ["numero"]

    def has_delete_permission(self, request, obj=None):
        return False

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.tipo = "CONVOCACAO"
            instance.save()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if models.is_admin_campus(request.user):
            return qs.filter(campus__in=request.user.lotacoes.all())
        else:
            return qs

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if not obj:
            edicoes = (
                models.Edicao.objects.filter(
                    processo_seletivo__sigla__in=["PSCT", "SiSU"]
                )
                .distinct()
                .order_by("processo_seletivo", "-ano", "-semestre", "nome")
            )
            form.base_fields["edicao"].queryset = edicoes
            form.base_fields["edicao"].choices = [(None, "--------")] + [
                (e.id, e) for e in edicoes
            ]

            if models.is_admin_campus(request.user):
                qs = Campus.objects.filter(id__in=request.user.lotacoes.all())
                form.base_fields["campus"].queryset = qs
                form.base_fields["campus"].choices = [(c.id, c) for c in qs]
            else:
                return form

        return form

    def has_change_permission(self, request, obj=None):
        perm = super().has_change_permission(request, obj)
        if obj:
            if models.is_admin_campus(request.user):
                return obj.campus in request.user.lotacoes.all()
        return perm

    class Media:
        css = {"all": ("ps/css/style_admin.css",)}


class ChamadaAdmin(CompareVersionAdmin):
    list_display = ("etapa", "curso", "modalidade", "vagas")
    ordering = ("-etapa", "curso", "modalidade")
    list_filter = (
        listfilters.ChamadaEtapaListFilter,
        listfilters.ChamadaEdicaoListFilter,
        listfilters.ChamadaCampusListFilter,
        listfilters.ChamadaCursoListFilter,
        listfilters.ChamadaTurnoListFilter,
        listfilters.ChamadaModalidadeListFilter,
    )
    search_fields = (
        "curso__campus__nome",
        "curso__curso__nome",
        "curso__turno",
        "modalidade__nome",
    )
    fieldsets = (
        (None, {"fields": ("etapa", "curso", "modalidade", "multiplicador", "vagas")}),
    )

    def get_readonly_fields(self, request, obj=None):
        r = ["vagas"]
        if obj:
            r.extend(["etapa", "curso", "modalidade", "vagas"])
            if obj.etapa.encerrada:
                r.append("multiplicador")
        return r

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if models.is_admin_campus(request.user):
            return qs.filter(curso__campus__in=request.user.lotacoes.all())
        else:
            return qs

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if not obj:
            if models.is_admin_campus(request.user):
                form.base_fields["curso"].queryset = CursoSelecao.objects.filter(
                    campus__in=request.user.lotacoes.all()
                )
            else:
                return form

        return form

    def has_change_permission(self, request, obj=None):
        perm = super().has_change_permission(request, obj)
        if obj:
            if models.is_admin_campus(request.user):
                return obj.curso.campus in request.user.lotacoes.all()
        return perm

    class Media:
        css = {"all": ("ps/css/style_admin.css",)}

    @transaction.atomic
    def delete_model(self, request, obj):
        obj.get_confirmacoes_interesse().delete()
        obj.get_analises_documentais().delete()
        super().delete_model(request, obj)


class TransicaoInlineFormSet(django_forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()
        arestas = []
        for form in self.forms:
            data = form.cleaned_data
            origem = data.get("origem")
            destino = data.get("destino")

            if origem and destino:
                arestas.append((origem, destino))

        if models.existe_ciclo(arestas):
            raise ValidationError("Exite um ciclo nas transições")

        return self


class TransicaoModalidadePossivelInline(admin.TabularInline):
    model = models.TransicaoModalidadePossivel
    formset = TransicaoInlineFormSet
    extra = 1


class TransicaoModalidadeAdmin(admin.ModelAdmin):
    inlines = [TransicaoModalidadePossivelInline]


class InscricaoAdmin(admin.ModelAdmin):
    search_fields = ("candidato__pessoa__nome",)
    list_display = ("candidato", "curso", "modalidade", "edicao")
    list_filter = ("curso", "modalidade", "edicao")
    readonly_fields = ("candidato", "curso", "modalidade", "edicao")
    exclude = ("chamada",)


class MatriculaAdmin(admin.ModelAdmin):
    search_fields = (
        "inscricao__candidato__pessoa__nome",
        "inscricao__candidato__pessoa__cpf",
    )
    list_display = ("inscricao", "modalidade")
    list_filter = (
        listfilters.MatriculaEdicaoListFilter,
        listfilters.MatriculaCursoListFilter,
        "inscricao__modalidade",
    )
    readonly_fields = ("inscricao", "etapa")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if models.is_admin_campus(request.user):
            try:
                return qs.filter(
                    inscricao__curso__campus__in=request.user.lotacoes.all()
                )
            except ObjectDoesNotExist:
                return qs.none()
        else:
            return qs


class VagaAdmin(CompareVersionAdmin):
    search_fields = ("candidato__pessoa__nome",)
    list_display = ("edicao", "curso", "candidato")
    list_filter = (
        listfilters.VagasEdicaoListFilter,
        listfilters.VagasCursoListFilter,
        "modalidade_primaria",
        "modalidade",
    )
    form = forms.VagaForm


class TipoAnaliseAdmin(admin.ModelAdmin):
    list_display = ("nome", "setor_responsavel", "descricao")
    exclude = ()


class AnaliseDocumentalInlineFormSet(django_forms.models.BaseInlineFormSet):
    def clean(self):

        super().clean()
        for form in self.forms:
            data = form.cleaned_data
            situacao = data.get("situacao")
            analise_documental = data.get("analise_documental")

            if situacao == "False" and analise_documental.situacao_final == True:
                raise ValidationError(
                    "A análise de documentos não pode ser deferida se houver avaliação indeferida."
                )

        return self


class AvaliacaoDocumentalInline(admin.StackedInline):
    model = models.AvaliacaoDocumental
    extra = 1
    form = forms.TipoAnaliseForm
    formset = AnaliseDocumentalInlineFormSet


class SituacaoListFilter(admin.BooleanFieldListFilter):
    def choices(self, changelist):
        for lookup, title in ((None, "Todas"), ("1", "Deferido"), ("0", "Indeferido")):
            yield {
                "selected": self.lookup_val == lookup and not self.lookup_val2,
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg: lookup}, [self.lookup_kwarg2]
                ),
                "display": title,
            }


class AnaliseDocumentalAdmin(admin.ModelAdmin):
    list_display = (
        "get_candidato",
        "get_cota",
        "get_curso",
        "get_edicao",
        "get_situacao_final",
        "observacao",
        "data",
    )
    list_filter = (
        listfilters.AnaliseDocumentalEdicaoListFilter,
        listfilters.AnaliseDocumentalCampusListFilter,
        listfilters.AnaliseDocumentalCursoListFilter,
        listfilters.AnaliseDocumentalModalidadeListFilter,
        ("situacao_final", SituacaoListFilter),
    )
    search_fields = ("confirmacao_interesse__inscricao__candidato__pessoa__nome",)
    inlines = [AvaliacaoDocumentalInline]
    form = forms.AnaliseDocumentalForm

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.user = request.user
        return form

    def get_candidato(self, obj):
        return obj.confirmacao_interesse.inscricao.candidato

    get_candidato.short_description = "Candidato da Análise"
    get_candidato.admin_order_field = "confirmacao_interesse__inscricao__candidato"

    def get_cota(self, obj):
        return obj.confirmacao_interesse.inscricao.modalidade

    get_cota.short_description = "Cota"
    get_cota.admin_order_field = "confirmacao_interesse__inscricao__modalidade"

    def get_curso(self, obj):
        return obj.confirmacao_interesse.inscricao.curso

    get_curso.short_description = "Curso"
    get_curso.admin_order_field = "confirmacao_interesse__inscricao__curso"

    def get_edicao(self, obj):
        return obj.confirmacao_interesse.inscricao.edicao

    get_edicao.short_description = "Processo Seletivo"
    get_edicao.admin_order_field = "confirmacao_interesse__inscricao__edicao"

    def get_situacao_final(self, obj):
        return format_html(
            '<span class="status status-{}">{}</span>',
            obj.get_situacao_final_display().lower(),
            obj.get_situacao_final_display(),
        )

    get_situacao_final.short_description = "Situação Final"
    get_situacao_final.admin_order_field = "situacao_final"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if models.is_admin_campus(request.user):
            return qs.filter(
                confirmacao_interesse__inscricao__curso__campus__in=request.user.lotacoes.all()
            )
        else:
            return qs

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.model.objects.get(pk=object_id)

        if not obj.is_deferida() and obj.is_analise_cota():
            inscricao_ampla = (
                obj.inscricoes_convocacoes_concomitantes()
                .filter(modalidade=ModalidadeEnum.ampla_concorrencia)
                .first()
            )
            if inscricao_ampla:
                if not extra_context:
                    extra_context = dict()
                extra_context.update({"inscricao_ampla_concomitante": inscricao_ampla})
        return super().change_view(request, object_id, form_url, extra_context)


class ConfirmacaoInteresseAdmin(admin.ModelAdmin):
    list_display = ("inscricao", "etapa", "get_formulario_matricula")
    list_display_icons = True
    list_filter = (
        listfilters.ConfirmacaoInteresseEtapaListFilter,
        listfilters.ConfirmacaoInteresseCursoListFilter,
        "inscricao__modalidade",
    )
    search_fields = ("inscricao__candidato__pessoa__nome",)
    actions = None
    form = forms.ConfirmacaoInteresseForm

    @mark_safe
    def get_formulario_matricula(self, obj):
        chamadas = Chamada.objects.filter(
            etapa=obj.etapa,
            modalidade=obj.inscricao.modalidade,
            inscricoes__id=obj.inscricao.id,
        )
        if chamadas.exists() and obj.etapa.manifestacao_interesse_gerenciada:
            url = reverse(
                "imprimir_prematricula",
                args=[obj.inscricao.candidato.pessoa.id, obj.inscricao.chamada.id],
            )
            return f'<a href="{url}" class="button">Imprimir</a>'
        else:
            return ""

    get_formulario_matricula.short_description = "Form. de Matrícula"

    def has_delete_permission(self, request, obj=None):
        if obj:
            return obj.pode_apagar()
        return super().has_delete_permission(request, obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if models.is_admin_campus(request.user):
            return qs.filter(inscricao__curso__campus__in=request.user.lotacoes.all())
        else:
            return qs


class RecursoAdmin(admin.ModelAdmin):
    list_display = (
        "get_candidato",
        "get_cota",
        "get_curso",
        "get_edicao",
        "protocolo",
        "justificativa",
        "get_status_recurso",
    )
    list_filter = (
        (
            "analise_documental__confirmacao_interesse__inscricao__edicao",
            admin.RelatedOnlyFieldListFilter,
        ),
        (
            "analise_documental__confirmacao_interesse__inscricao__curso__campus",
            admin.RelatedOnlyFieldListFilter,
        ),
        listfilters.RecursosCursoListFilter,
        "analise_documental__confirmacao_interesse__inscricao__modalidade",
        "status_recurso",
    )
    search_fields = (
        "analise_documental__confirmacao_interesse__inscricao__candidato__pessoa__nome",
        "protocolo",
        "justificativa",
    )
    form = forms.RecursoForm

    def get_candidato(self, obj):
        return obj.analise_documental.confirmacao_interesse.inscricao.candidato

    get_candidato.short_description = "Candidato do Recurso"
    get_candidato.admin_order_field = (
        "analise_documental__confirmacao_interesse__inscricao__candidato"
    )

    def get_cota(self, obj):
        return obj.analise_documental.confirmacao_interesse.inscricao.modalidade

    get_cota.short_description = "Cota"
    get_cota.admin_order_field = (
        "analise_documental__confirmacao_interesse__inscricao__modalidade"
    )

    def get_curso(self, obj):
        return obj.analise_documental.confirmacao_interesse.inscricao.curso

    get_curso.short_description = "Curso"
    get_curso.admin_order_field = (
        "analise_documental__confirmacao_interesse__inscricao__curso"
    )

    def get_edicao(self, obj):
        return obj.analise_documental.confirmacao_interesse.inscricao.edicao

    get_edicao.short_description = "Processo Seletivo"
    get_edicao.admin_order_field = (
        "analise_documental__confirmacao_interesse__inscricao__edicao"
    )

    def get_status_recurso(self, obj):
        return format_html(
            '<span class="status status-{}">{}</span>',
            obj.status_recurso.lower(),
            obj.status_recurso.capitalize(),
        )

    get_status_recurso.short_description = "Status"
    get_status_recurso.admin_order_field = "status_recurso"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if models.is_admin_campus(request.user):
            return qs.filter(
                analise_documental__confirmacao_interesse__inscricao__curso__campus__in=request.user.lotacoes.all()
            )
        else:
            return qs


admin.site.register(models.Modalidade, PermissionCompareVersionAdmin)
admin.site.register(models.ProcessoSeletivo, ProcessoSeletivoAdmin)
admin.site.register(models.Edicao, EdicaoAdmin)
admin.site.register(models.Etapa, EtapaAdmin)
admin.site.register(models.Chamada, ChamadaAdmin)
admin.site.register(models.TransicaoModalidade, TransicaoModalidadeAdmin)
admin.site.register(models.Inscricao, InscricaoAdmin)
admin.site.register(models.Matricula, MatriculaAdmin)
admin.site.register(models.Vaga, VagaAdmin)
admin.site.register(models.AnaliseDocumental, AnaliseDocumentalAdmin)
admin.site.register(models.TipoAnalise, TipoAnaliseAdmin)
admin.site.register(models.ConfirmacaoInteresse, ConfirmacaoInteresseAdmin)
admin.site.register(models.Recurso, RecursoAdmin)
