from django.contrib import admin

from editais import models
from editais.forms import EditalForm, PeriodoSelecaoInlineForm
from editais.models import Documento


class NivelSelecaoInline(admin.StackedInline):
    model = models.NivelSelecao
    min_num = 1
    extra = 0


class PeriodoSelecaoInline(admin.StackedInline):
    exclude = ("inscricao",)
    model = models.PeriodoSelecao
    min_num = 1
    extra = 0
    form = PeriodoSelecaoInlineForm

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(inscricao=True)


class DocumentoInline(admin.StackedInline):
    model = Documento
    extra = 1


@admin.register(models.Edital)
class EditalAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "numero",
        "ano",
        "setor_responsavel",
        "tipo",
        "publicado",
        "encerrado",
    )
    list_filter = (
        "edicao__processo_seletivo",
        ("edicao", admin.RelatedOnlyFieldListFilter),
        "numero",
        "ano",
        "tipo",
        "publicado",
    )
    search_fields = ("nome", "numero", "ano")
    inlines = [NivelSelecaoInline, DocumentoInline, PeriodoSelecaoInline]
    model = models.Edital
    form = EditalForm
    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    ("nome"),
                    ("numero", "ano", "data_publicacao"),
                    ("edicao"),
                    ("tipo", "setor_responsavel"),
                    ("descricao"),
                    ("url_video_descricao"),
                    ("palavra_chave"),
                )
            },
        ),
        (
            "Inscrições",
            {
                "fields": (
                    ("inscricao_inicio"),
                    ("inscricao_fim"),
                    ("prazo_pagamento"),
                    ("link_inscricoes"),
                )
            },
        ),
        ("Situação", {"fields": (("publicado", "encerrado"),)}),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["numero", "ano", "data_publicacao", "retificado"]
        return super().get_readonly_fields(request, obj)

    def get_fieldsets(self, request, obj=None):
        if (obj and obj.retificado) or "retificado" in request.GET:
            return (
                (
                    "Identificação",
                    {
                        "fields": (
                            ("nome"),
                            ("numero", "ano", "data_publicacao"),
                            ("tipo"),
                            ("retificado"),
                            ("publicado"),
                        )
                    },
                ),
            )
        return super().get_fieldsets(request, obj)

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            # hide PeriodoSelecaoInLine in the add view
            if "retificado" in request.GET or (obj and obj.retificado is not None):
                if isinstance(inline, PeriodoSelecaoInline) or isinstance(
                    inline, NivelSelecaoInline
                ):
                    continue
            yield inline.get_formset(request, obj), inline

    def save_model(self, request, obj, form, change):
        if "retificado" in request.GET:
            pk_retificado = request.GET.get("retificado")
            edital = models.Edital.objects.get(pk=pk_retificado)
            obj.edicao = edital.edicao
            obj.setor_responsavel = edital.setor_responsavel
            obj.descricao = edital.descricao
            obj.prazo_pagamento = edital.prazo_pagamento
            obj.link_inscricoes = edital.link_inscricoes
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        inicio = form.cleaned_data.get("inscricao_inicio")
        fim = form.cleaned_data.get("inscricao_fim")
        periodo_inscricao, created = models.PeriodoSelecao.objects.get_or_create(
            inscricao=True,
            tipo="SELECAO",
            edital=form.instance,
            defaults={"nome": "Inscrições", "inicio": inicio, "fim": fim},
        )
        if not created:
            periodo_inscricao.inicio = form.cleaned_data.get("inscricao_inicio")
            periodo_inscricao.fim = form.cleaned_data.get("inscricao_fim")
            periodo_inscricao.save()

        super().save_related(request, form, formsets, change)
