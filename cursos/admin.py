from datetime import datetime

from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from registration import utils
from . import choices
from . import forms
from . import models


class ObrigatorioInline(admin.TabularInline):
    extra = 1
    formset = forms.ObrigatorioInlineFormSet

    def get_min_num(self, request, obj=None, **kwargs):
        if obj and obj.publicado:
            return 1
        return 0


class CoordenacaoInline(admin.StackedInline):
    form = forms.CoordenacaoForm
    model = models.Coordenacao
    min_num = 1
    fields = ("coordenador", "telefone", "email", "substituto")


class AtoRegulatorioInline(ObrigatorioInline):
    model = models.AtoRegulatorio
    fields = ("tipo", "numero", "ano", "descricao", "arquivo")


class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "obrigatorio_tecnico",
        "obrigatorio_graduacao",
        "obrigatorio_pos_graduacao",
    )
    ordering = ("nome",)
    actions = (
        "tornar_obrigatorio_tecnico",
        "tornar_opcional_tecnico",
        "tornar_obrigatorio_graduacao",
        "tornar_opcional_graduacao",
        "tornar_obrigatorio_pos_graduacao",
        "tornar_opcional_pos_graduacao",
    )

    def formatar_mensagem(self, rows_alteradas, obrigatorio):
        mensagem = ""
        if rows_alteradas == 1:
            if obrigatorio:
                mensagem = "1 item foi modificado para obrigatório com sucesso"
            else:
                mensagem = "1 item foi modificado para opcional com sucesso"
        else:
            if obrigatorio:
                mensagem = f"{rows_alteradas} itens foram modificados para obrigatórios com sucesso"
            else:
                mensagem = f"{rows_alteradas} itens foram modificados para opcionais com sucesso"
        return mensagem

    def tornar_obrigatorio_tecnico(self, request, queryset):
        rows_updated = queryset.update(obrigatorio_tecnico=True)
        self.message_user(
            request,
            self.formatar_mensagem(rows_alteradas=rows_updated, obrigatorio=True),
        )

    tornar_obrigatorio_tecnico.short_description = (
        "Tornar obrigatórios para cursos técnicos os Tipos de Documentos selecionados."
    )

    def tornar_opcional_tecnico(self, request, queryset):
        rows_updated = queryset.update(obrigatorio_tecnico=False)
        self.message_user(
            request,
            self.formatar_mensagem(rows_alteradas=rows_updated, obrigatorio=False),
        )

    tornar_opcional_tecnico.short_description = (
        "Tornar opcionais para cursos técnicos os Tipos de Documentos selecionados."
    )

    def tornar_obrigatorio_graduacao(self, request, queryset):
        rows_updated = queryset.update(obrigatorio_graduacao=True)
        self.message_user(
            request,
            self.formatar_mensagem(rows_alteradas=rows_updated, obrigatorio=True),
        )

    tornar_obrigatorio_graduacao.short_description = "Tornar obrigatórios para cursos de graduação os Tipos de Documentos selecionados."

    def tornar_opcional_graduacao(self, request, queryset):
        rows_updated = queryset.update(obrigatorio_graduacao=False)
        self.message_user(
            request,
            self.formatar_mensagem(rows_alteradas=rows_updated, obrigatorio=False),
        )

    tornar_opcional_graduacao.short_description = (
        "Tornar opcionais para cursos de graduação os Tipos de Documentos selecionados."
    )

    def tornar_obrigatorio_pos_graduacao(self, request, queryset):
        rows_updated = queryset.update(obrigatorio_pos_graduacao=True)
        self.message_user(
            request,
            self.formatar_mensagem(rows_alteradas=rows_updated, obrigatorio=True),
        )

    tornar_obrigatorio_pos_graduacao.short_description = "Tornar obrigatórios para cursos de pós-graduação os Tipos de Documentos selecionados."

    def tornar_opcional_pos_graduacao(self, request, queryset):
        rows_updated = queryset.update(obrigatorio_pos_graduacao=False)
        self.message_user(
            request,
            self.formatar_mensagem(rows_alteradas=rows_updated, obrigatorio=False),
        )

    tornar_opcional_pos_graduacao.short_description = "Tornar opcionais para cursos de pós-graduação os Tipos de Documentos selecionados."


class DocumentoInline(ObrigatorioInline):
    model = models.Documento
    fields = ("tipo", "descricao", "arquivo")
    formset = forms.DocumentoInlineFormSet

    def get_min_num(self, request, obj=None, **kwargs):
        if obj and obj.publicado and obj.documentos_obrigatorios:
            return 1
        return 0


class DisciplinaCursoInline(ObrigatorioInline):
    form = forms.DisciplinaCurso
    formset = forms.DisciplinaInlineFormSet
    model = models.DisciplinaCurso
    fields = ("periodo", "disciplina", "ch", "docentes", "plano")


class VagaCursoInLine(ObrigatorioInline):
    model = models.VagaCurso
    fields = ("vagas_s1", "vagas_s2", "polo")


class CursoNoCampusAdmin(admin.ModelAdmin):
    form = forms.CursoNoCampusForm
    list_display = (
        "curso",
        "formacao",
        "turno",
        "modalidade",
        "coordenacao_display",
        "campus",
        "publicado",
        "excluido",
    )
    ordering = ("curso__nome",)
    search_fields = ("curso__nome", "campus__nome", "codigo")
    list_filter = ("campus", "modalidade", "formacao", "turno", "excluido")
    inlines = [
        # CoordenacaoInline,
        # VagaCursoInLine,
        # AtoRegulatorioInline,
        # DocumentoInline,
        # DisciplinaCursoInline,
    ]
    fieldsets = (
        (
            "IDENTIFICAÇÃO",
            {
                "fields": (
                    "curso",
                    "modalidade",
                    "campus",
                    "formacao",
                    "turno",
                    "publicado",
                    "excluido",
                )
            },
        ),
        (
            "INFORMAÇÕES BÁSICAS",
            {
                "classes": ("collapse",),
                "fields": (
                    "perfil",
                    "perfil_libras",
                    "video_catalogo",
                    ("codigo", "codigo_nao_se_aplica"),
                    "codigo_suap",
                    "inicio",
                    "termino",
                    ("conceito", "conceito_nao_se_aplica"),
                    ("cpc", "cpc_nao_se_aplica"),
                    ("enade", "enade_nao_se_aplica"),
                    "ch_minima",
                    ("ch_estagio", "ch_estagio_nao_se_aplica"),
                    ("ch_tcc", "ch_tcc_nao_se_aplica"),
                    ("ch_rel_estagio", "ch_rel_estagio_nao_se_aplica"),
                    ("ch_pratica_docente", "ch_pratica_docente_nao_se_aplica"),
                    ("ch_atividades_comp", "ch_atividades_comp_nao_se_aplica"),
                    ("periodo_min_int", "periodo_min_int_nao_se_aplica"),
                    ("forma_acesso", "palavras_chave"),
                ),
            },
        ),
    )

    class Media:
        js = ("js/curso_no_campus_admin.js",)

    def coordenacao_display(self, obj):
        coordenadores = "-"
        if hasattr(obj, "coordenacao"):
            coordenadores = f"{obj.coordenacao.coordenador}"
            if obj.coordenacao.substituto:
                coordenadores = f"{coordenadores} e {obj.coordenacao.substituto}"
        return coordenadores

    coordenacao_display.short_description = "Coordenadores"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        user = request.user
        if user.is_superuser or utils.is_admin_sistemico_cursos(user):
            return queryset
        cursos_pos = self.model.objects.none()
        cursos_dde = self.model.objects.none()
        cursos_admin_campus = self.model.objects.none()
        cursos_coordenacao = self.model.objects.none()
        if utils.is_admin_sistemico_cursos_pos(user):
            cursos_pos = queryset.filter(curso__nivel_formacao="POSGRADUACAO")
        if utils.is_diretor_ensino(user):
            diretor = models.Servidor.get_by_user(user)
            if diretor:
                cursos_dde = queryset.filter(
                    Q(campus__diretor_ensino=diretor)
                    | Q(campus__diretor_ensino_substituto=diretor)
                )
        if utils.is_administrador_cursos_campus(user):
            campi_lotacao = user.lotacoes.all()
            cursos_admin_campus = queryset.filter(campus__in=campi_lotacao)
        if utils.is_coordenador_curso(user):
            coordenacoes = models.Coordenacao.get_by_user(user)
            if coordenacoes.exists():
                cursos_coordenacao = queryset.filter(coordenacao__in=coordenacoes)
        return (
            cursos_pos | cursos_dde | cursos_admin_campus | cursos_coordenacao
        ).distinct()

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            # torna o campo de coordenador somente leitura se o user não tiver permissão de alterá-lo
            if isinstance(inline, CoordenacaoInline):
                if obj and not obj.is_administrador_curso(request.user):
                    inline.readonly_fields = ["coordenador"]
                else:
                    inline.readonly_fields = []
            yield inline.get_formset(request, obj), inline

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        eh_diretor = utils.is_diretor_ensino(request.user)
        eh_administrador_campus = utils.is_administrador_cursos_campus(request.user)
        if eh_diretor or eh_administrador_campus:
            query_args = Q(servidores=request.user)
            diretor = models.Servidor.get_by_user(request.user)
            if diretor:
                query_args |= Q(diretor_ensino=diretor) | Q(
                    diretor_ensino_substituto=diretor
                )
            campi = models.Campus.objects.filter(query_args).distinct()
            if request.user.is_superuser:
                campi = models.Campus.objects.all()
            form.base_fields["campus"].queryset = campi
        elif utils.is_admin_sistemico_cursos_pos(request.user):
            form.base_fields["curso"].queryset = models.Curso.objects.filter(
                nivel_formacao="POSGRADUACAO"
            )
            formacao_choices = []
            for k, v in choices.Formacao.choices():
                if k in ["MESTRADO", "ESPECIALIZACAO", "DOUTORADO"]:
                    formacao_choices += [(k, v)]
            form.base_fields["formacao"].choices = [
                ("---------", "---------")
            ] + formacao_choices
        return form

    def get_readonly_fields(self, request, obj=None):
        if obj and not obj.is_administrador_curso(request.user):
            return ["formacao", "curso", "campus", "modalidade", "turno"]
        if not obj:
            return ["publicado"]
        return []

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            if isinstance(obj, models.DisciplinaCurso):
                obj.curso.disciplinas_atualizacao = datetime.now()
                obj.curso.save()
            obj.delete()
        for instance in instances:
            if isinstance(instance, models.DisciplinaCurso):
                instance.curso.disciplinas_atualizacao = datetime.now()
                instance.curso.save()
            instance.save()
        formset.save_m2m()


@admin.register(models.Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ("nome", "matricula", "tipo")
    ordering = ("nome",)
    search_fields = ("nome",)
    fields = ("nome", "matricula", "tipo", "admissao", "lattes", "titulacao")


@admin.register(models.Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = ("nome", "titulacao", "admissao", "rt", "lattes")
    ordering = ("titulacao", "admissao", "rt", "nome")
    search_fields = ("nome",)
    readonly_fields = ("nome", "matricula", "admissao", "lattes", "rt")

    fieldsets = (
        (
            None,
            {"fields": ("nome", "matricula", "admissao", "lattes", "rt", "titulacao")},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).docentes()


@admin.register(models.DocenteExterno)
class DocenteExternoAdmin(admin.ModelAdmin):
    form = forms.DocenteExternoForm
    list_display = ("nome", "titulacao", "lattes")
    ordering = ("titulacao", "nome")
    search_fields = ("nome",)

    fieldsets = ((None, {"fields": ("nome", "matricula", "lattes", "titulacao")}),)

    def get_queryset(self, request):
        return super().get_queryset(request).docentes_externos()


class CidadeAdmin(admin.ModelAdmin):
    ordering = ("uf", "nome")


class CampusAdmin(admin.ModelAdmin):
    ordering = ("nome", "sigla")
    list_display = ("nome", "sigla", "diretor_ensino", "telefone", "endereco", "cidade")
    form = forms.CampusForm
    fields = (
        "sigla",
        "nome",
        "ies",
        "cidade",
        "endereco",
        "telefone",
        "aparece_no_menu",
        "url",
        "mapa",
        "diretor_ensino",
        "diretor_ensino_substituto",
    )

    def get_queryset(self, request):
        try:
            if request.user.is_superuser or utils.is_admin_sistemico_cursos(
                request.user
            ):
                return super().get_queryset(request)
            elif utils.is_diretor_ensino(request.user):
                diretor = models.Servidor.get_by_user(request.user)
                return self.model.objects.filter(
                    Q(diretor_ensino=diretor) | Q(diretor_ensino_substituto=diretor)
                ).distinct()
            else:
                return self.model.objects.none()
        except ObjectDoesNotExist:
            return self.model.objects.none()

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser or utils.is_admin_sistemico_cursos(request.user):
            return []
        elif obj and obj.diretor_ensino.user == request.user:
            return ["diretor_ensino"]
        else:
            return ["diretor_ensino", "diretor_ensino_substituto"]

    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.fields + ("servidores",)
        return self.fields


class PoloAdmin(admin.ModelAdmin):
    form = forms.PoloForm
    list_display = ("cidade", "endereco", "telefone", "horario_funcionamento")
    ordering = ["cidade__nome"]


class CursoAdmin(admin.ModelAdmin):
    ordering = ["nome"]
    form = forms.CursoForm

    def get_queryset(self, request):
        user = request.user
        try:
            if user.is_superuser:
                return self.model.objects.all()
            if utils.is_admin_sistemico_cursos_pos(user):
                return self.model.objects.filter(nivel_formacao="POSGRADUACAO")
            elif utils.is_diretor_ensino(user):
                return self.model.objects.exclude(nivel_formacao="POSGRADUACAO")
        except ObjectDoesNotExist:
            return self.model.objects.none()
        return super().get_queryset(request)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj=None, **kwargs)
        nivel_choices = []
        if utils.is_diretor_ensino(request.user):
            for k, v in choices.NivelFormacao.choices():
                if k not in ["POSGRADUACAO"]:
                    nivel_choices += [(k, v)]
            form.base_fields["nivel_formacao"].choices = [
                ("---------", "---------")
            ] + nivel_choices
        elif utils.is_admin_sistemico_cursos_pos(request.user):
            for k, v in choices.NivelFormacao.choices():
                if k in ["POSGRADUACAO"]:
                    nivel_choices += [(k, v)]
            form.base_fields["nivel_formacao"].choices = [
                ("---------", "---------")
            ] + nivel_choices
        return form


class DisciplinaAdmin(admin.ModelAdmin):
    ordering = ("nome",)
    search_fields = ("nome",)


admin.site.register(models.CursoSelecao, CursoNoCampusAdmin)
admin.site.register(models.Campus, CampusAdmin)
admin.site.register(models.IES)
admin.site.register(models.TipoAtoRegulatorio)
admin.site.register(models.TipoDocumento, TipoDocumentoAdmin)
admin.site.register(models.Cidade, CidadeAdmin)
admin.site.register(models.Disciplina, DisciplinaAdmin)
admin.site.register(models.Polo, PoloAdmin)
admin.site.register(models.Curso, CursoAdmin)
