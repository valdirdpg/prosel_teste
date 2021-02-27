from django.contrib import admin

from cursos.models import Campus, CursoSelecao
from processoseletivo import models


class EtapaEdicaoListFilter(admin.SimpleListFilter):
    title = "Edicao"
    parameter_name = "edicao"

    def lookups(self, request, model_admin):
        pk_etapas = (
            model_admin.get_queryset(request).distinct().values_list("pk", flat=True)
        )
        filtros = {"etapa__in": pk_etapas}

        numero = request.GET.get("numero")
        if numero and numero.isdigit():
            filtros.update(etapa__numero=numero)

        campus_id = request.GET.get("campus")
        if campus_id and campus_id.isdigit():
            filtros.update(etapa__campus=campus_id)

        edicoes = (
            models.Edicao.objects.filter(**filtros)
            .order_by("processo_seletivo", "ano", "semestre", "nome")
            .distinct()
        )

        return [(edicao.id, edicao) for edicao in edicoes]

    def queryset(self, request, queryset):
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(edicao=value)
        return queryset


class EtapaCampusListFilter(admin.SimpleListFilter):
    title = "Campus"
    parameter_name = "campus"

    def lookups(self, request, model_admin):
        campi = (
            Campus.objects.filter(etapa__isnull=False)
            .order_by("nome", "sigla")
            .distinct()
        )

        filtros = {}

        edicao_id = request.GET.get("edicao")
        if edicao_id and edicao_id.isdigit():
            filtros.update(etapa__edicao=edicao_id)

        numero = request.GET.get("numero")
        if numero and numero.isdigit():
            filtros.update(etapa__numero=numero)

        campi = campi.filter(**filtros)

        return [(c.id, c) for c in campi]

    def queryset(self, request, queryset):
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(campus=value)
        return queryset


class EtapaNumeroListFilter(admin.SimpleListFilter):
    title = "Número da Etapa"
    parameter_name = "numero"

    def lookups(self, request, model_admin):
        numeros = (
            models.Etapa.objects.values_list("numero", flat=True)
            .order_by("numero")
            .distinct()
        )

        filtros = {}

        edicao_id = request.GET.get("edicao")
        if edicao_id and edicao_id.isdigit():
            filtros.update(edicao=edicao_id)

        campus_id = request.GET.get("campus")
        if campus_id and campus_id.isdigit():
            filtros.update(campus=campus_id)

        numeros = numeros.filter(**filtros)

        return [(numero, numero) for numero in numeros]

    def queryset(self, request, queryset):
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(numero=value)
        return queryset


class ChamadaEtapaListFilter(admin.SimpleListFilter):
    title = "Etapa"
    parameter_name = "etapa"

    def lookups(self, request, model_admin):
        pk_chamadas = (
            model_admin.get_queryset(request).distinct().values_list("pk", flat=True)
        )
        filtros = {"chamadas__in": pk_chamadas}

        edicao_id = request.GET.get("edicao")
        if edicao_id and edicao_id.isdigit():
            filtros.update(edicao=edicao_id)

        campus_id = request.GET.get("campus")
        if campus_id and campus_id.isdigit():
            filtros.update(campus=campus_id)

        curso_id = request.GET.get("curso")
        if curso_id and curso_id.isdigit():
            filtros.update(chamadas__curso=curso_id)

        turno = request.GET.get("turno")
        if turno:
            filtros.update(chamadas__curso__turno=turno)

        modalidade_id = request.GET.get("modalidade")
        if modalidade_id and modalidade_id.isdigit():
            filtros.update(chamadas__modalidade=modalidade_id)

        etapas = (
            models.Etapa.objects.filter(**filtros)
            .order_by(
                "edicao__processo_seletivo",
                "-edicao__ano",
                "-edicao__semestre",
                "edicao__nome",
                "numero",
                "campus",
            )
            .distinct()
        )

        return [(etapa.id, etapa) for etapa in etapas]

    def queryset(self, request, queryset):
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(etapa=value)
        return queryset


class ChamadaEdicaoListFilter(admin.SimpleListFilter):
    title = "Edicao"
    parameter_name = "edicao"

    def lookups(self, request, model_admin):
        pk_chamadas = (
            model_admin.get_queryset(request).distinct().values_list("pk", flat=True)
        )
        filtros = {"etapa__chamadas__in": pk_chamadas}

        etapa_id = request.GET.get("etapa")
        if etapa_id and etapa_id.isdigit():
            filtros.update(etapa=etapa_id)

        campus_id = request.GET.get("campus")
        if campus_id and campus_id.isdigit():
            filtros.update(etapa__campus=campus_id)

        curso_id = request.GET.get("curso")
        if curso_id and curso_id.isdigit():
            filtros.update(inscricao__curso=curso_id)

        turno = request.GET.get("turno")
        if turno:
            filtros.update(etapa__chamadas__curso__turno=turno)

        modalidade_id = request.GET.get("modalidade")
        if modalidade_id and modalidade_id.isdigit():
            filtros.update(vagas__modalidade=modalidade_id)

        edicoes = (
            models.Edicao.objects.filter(**filtros)
            .order_by("processo_seletivo", "ano", "semestre", "nome")
            .distinct()
        )

        return [(edicao.id, edicao) for edicao in edicoes]

    def queryset(self, request, queryset):
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(etapa__edicao=value)
        return queryset


class ChamadaCampusListFilter(admin.SimpleListFilter):
    title = "Campus"
    parameter_name = "campus"

    def lookups(self, request, model_admin):
        pk_chamadas = (
            model_admin.get_queryset(request).distinct().values_list("pk", flat=True)
        )
        filtros = {"cursonocampus__cursoselecao__chamada__in": pk_chamadas}

        etapa_id = request.GET.get("etapa")
        if etapa_id and etapa_id.isdigit():
            filtros.update(cursonocampus__campus__etapa__pk=etapa_id)

        edicao_id = request.GET.get("edicao")
        if edicao_id and edicao_id.isdigit():
            filtros.update(cursonocampus__vaga__edicao=edicao_id)

        curso_id = request.GET.get("curso")
        if curso_id and curso_id.isdigit():
            filtros.update(etapa__chamadas__curso=curso_id)

        turno = request.GET.get("turno")
        if turno:
            filtros.update(cursonocampus__turno=turno)

        modalidade_id = request.GET.get("modalidade")
        if modalidade_id and modalidade_id.isdigit():
            filtros.update(etapa__chamadas__modalidade=modalidade_id)

        campi = Campus.objects.filter(**filtros).order_by("nome").distinct()

        return [(c.id, c) for c in campi]

    def queryset(self, request, queryset):
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(etapa__campus=value)
        return queryset


class ChamadaCursoListFilter(admin.SimpleListFilter):
    title = "Curso"
    parameter_name = "curso"

    def lookups(self, request, model_admin):
        pk_chamadas = (
            model_admin.get_queryset(request).distinct().values_list("pk", flat=True)
        )
        filtros = {"chamada__in": pk_chamadas}

        etapa_id = request.GET.get("etapa")
        if etapa_id and etapa_id.isdigit():
            filtros.update(chamada__etapa=etapa_id)

        edicao_id = request.GET.get("edicao")
        if edicao_id and edicao_id.isdigit():
            filtros.update(chamada__etapa__edicao=edicao_id)

        campus_id = request.GET.get("campus")
        if campus_id and campus_id.isdigit():
            filtros.update(campus=campus_id)

        turno = request.GET.get("turno")
        if turno:
            filtros.update(chamada__curso__turno=turno)

        modalidade_id = request.GET.get("modalidade")
        if modalidade_id and modalidade_id.isdigit():
            filtros.update(chamada__modalidade=modalidade_id)

        cursos = (
            CursoSelecao.objects.filter(**filtros)
            .ordena_por_formacao("curso__nome", "modalidade", "turno", "campus__nome")
            .distinct()
        )

        return [(curso.id, curso) for curso in cursos]

    def queryset(self, request, queryset):
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(curso=value)
        return queryset


class ChamadaTurnoListFilter(admin.SimpleListFilter):
    title = "Turno"
    parameter_name = "turno"

    def lookups(self, request, model_admin):
        turnos = (
            CursoSelecao.objects.distinct("turno")
            .order_by("turno")
            .values_list("turno", flat=True)
        )

        filtros = {}

        etapa_id = request.GET.get("etapa")
        if etapa_id and etapa_id.isdigit():
            filtros.update(chamada__etapa=etapa_id)

        edicao_id = request.GET.get("edicao")
        if edicao_id and edicao_id.isdigit():
            filtros.update(chamada__etapa__edicao=edicao_id)

        campus_id = request.GET.get("campus")
        if campus_id and campus_id.isdigit():
            filtros.update(campus=campus_id)

        curso_id = request.GET.get("curso")
        if curso_id and curso_id.isdigit():
            filtros.update(curso=curso_id)

        modalidade_id = request.GET.get("modalidade")
        if modalidade_id and modalidade_id.isdigit():
            filtros.update(chamada__modalidade=modalidade_id)

        turnos = turnos.filter(**filtros)

        return [(t, t) for t in turnos]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(curso__turno=value)
        return queryset


class ChamadaModalidadeListFilter(admin.SimpleListFilter):
    title = "Modalidade de cota"
    parameter_name = "modalidade"

    def lookups(self, request, model_admin):
        modalidades = (
            models.Modalidade.objects.filter(chamada__isnull=False)
            .distinct()
            .order_by("nome")
        )

        filtros = {}

        etapa_id = request.GET.get("etapa")
        if etapa_id and etapa_id.isdigit():
            filtros.update(chamada__etapa=etapa_id)

        edicao_id = request.GET.get("edicao")
        if edicao_id and edicao_id.isdigit():
            filtros.update(chamada__etapa__edicao=edicao_id)

        campus_id = request.GET.get("campus")
        if campus_id and campus_id.isdigit():
            filtros.update(chamada__etapa__campus=campus_id)

        curso_id = request.GET.get("curso")
        if curso_id and curso_id.isdigit():
            filtros.update(chamada__curso=curso_id)

        modalidades = modalidades.filter(**filtros)

        return [(m.id, m) for m in modalidades]

    def queryset(self, request, queryset):
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(modalidade=value)
        return queryset


class InscricaoCursoListFilter(admin.SimpleListFilter):
    title = "Curso"
    parameter_name = "curso"

    def lookups(self, request, model_admin):
        cursos = (
            CursoSelecao.objects.filter(inscricoes_mec__isnull=False)
            .ordena_por_formacao("curso__nome", "modalidade", "turno", "campus__nome")
            .distinct()
        )
        return [(curso.id, curso) for curso in cursos]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(curso=value)
        return queryset


class InscricaoEdicaoListFilter(admin.SimpleListFilter):
    title = "Edicao"
    parameter_name = "edicao"

    def lookups(self, request, model_admin):
        edicoes = (
            models.Edicao.objects.filter(inscricao__isnull=False)
            .order_by("processo_seletivo", "ano", "semestre", "nome")
            .distinct()
        )
        return [(edicao.id, edicao) for edicao in edicoes]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(edicao=value)
        return queryset


class MatriculaEdicaoListFilter(admin.SimpleListFilter):
    title = "Edicao"
    parameter_name = "edicao"

    def lookups(self, request, model_admin):
        edicoes = (
            models.Edicao.objects.filter(inscricao__matricula__isnull=False)
            .order_by("processo_seletivo", "ano", "semestre", "nome")
            .distinct()
        )
        return [(edicao.id, edicao) for edicao in edicoes]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(inscricao__edicao=value)
        return queryset


class MatriculaCursoListFilter(admin.SimpleListFilter):
    title = "Curso"
    parameter_name = "curso"

    def lookups(self, request, model_admin):
        cursos = (
            CursoSelecao.objects.filter(inscricoes_mec__matricula__isnull=False)
            .ordena_por_formacao("curso__nome", "modalidade", "turno", "campus__nome")
            .distinct()
        )
        return [(curso.id, curso) for curso in cursos]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(inscricao__curso=value)
        return queryset


class VagasEdicaoListFilter(admin.SimpleListFilter):
    title = "Edicao"
    parameter_name = "edicao"

    def lookups(self, request, model_admin):
        edicoes = (
            models.Edicao.objects.filter(vagas__isnull=False)
            .order_by("processo_seletivo", "ano", "semestre", "nome")
            .distinct()
        )
        return [(edicao.id, edicao) for edicao in edicoes]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(edicao=value)
        return queryset


class VagasCursoListFilter(admin.SimpleListFilter):
    title = "Curso"
    parameter_name = "curso"

    def lookups(self, request, model_admin):
        cursos = (
            CursoSelecao.objects.filter(vaga__isnull=False)
            .ordena_por_formacao("curso__nome", "modalidade", "turno", "campus__nome")
            .distinct()
        )
        return [(curso.id, curso) for curso in cursos]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(curso=value)
        return queryset


class AnaliseDocumentalEdicaoListFilter(admin.SimpleListFilter):
    title = "Edicao"
    parameter_name = "edicao"

    def lookups(self, request, model_admin):
        pk_analises = (
            model_admin.get_queryset(request).distinct().values_list("pk", flat=True)
        )
        filtros = {
            "inscricao__confirmacaointeresse__analisedocumental__in": pk_analises
        }

        campus_id = request.GET.get("campus")
        if campus_id and campus_id.isdigit():
            filtros.update(etapa__campus=campus_id)

        curso_id = request.GET.get("curso")
        if curso_id and curso_id.isdigit():
            filtros.update(etapa__chamadas__curso=curso_id)

        edicoes = (
            models.Edicao.objects.filter(**filtros)
            .order_by("processo_seletivo", "ano", "semestre", "nome")
            .distinct()
        )

        return [(edicao.id, edicao) for edicao in edicoes]

    def queryset(self, request, queryset):
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(confirmacao_interesse__inscricao__edicao=value)
        return queryset


class AnaliseDocumentalCampusListFilter(admin.SimpleListFilter):
    title = "Campus"
    parameter_name = "campus"

    def lookups(self, request, model_admin):
        pk_analises = (
            model_admin.get_queryset(request).distinct().values_list("pk", flat=True)
        )
        filtros = {"etapa__confirmacoes_interesse__analisedocumental__in": pk_analises}

        edicao_id = request.GET.get("edicao")
        if edicao_id and edicao_id.isdigit():
            filtros.update(etapa__edicao=edicao_id)

        curso_id = request.GET.get("curso")
        if curso_id and curso_id.isdigit():
            filtros.update(cursonocampus__curso=curso_id)

        modalidade_id = request.GET.get("modalidade")
        if modalidade_id and modalidade_id.isdigit():
            filtros.update(cursonocampus__chamada__modalidade=modalidade_id)

        campi = Campus.objects.filter(**filtros).order_by("nome", "cidade").distinct()

        return [(c.id, c) for c in campi]

    def queryset(self, request, queryset):
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(confirmacao_interesse__etapa__campus=value)
        return queryset


class AnaliseDocumentalCursoListFilter(admin.SimpleListFilter):
    title = "Curso"
    parameter_name = "curso"

    def lookups(self, request, model_admin):
        pk_analises = (
            model_admin.get_queryset(request).distinct().values_list("pk", flat=True)
        )
        filtros = {
            "inscricoes_mec__confirmacaointeresse__analisedocumental__in": pk_analises
        }

        edicao_id = request.GET.get("edicao")
        if edicao_id and edicao_id.isdigit():
            filtros.update(chamada__etapa__edicao=edicao_id)

        campus_id = request.GET.get("campus")
        if campus_id and campus_id.isdigit():
            filtros.update(campus=campus_id)

        modalidade_id = request.GET.get("modalidade")
        if modalidade_id and modalidade_id.isdigit():
            filtros.update(chamada__modalidade=modalidade_id)

        cursos = (
            CursoSelecao.objects.filter(**filtros)
            .ordena_por_formacao("curso__nome", "modalidade", "turno", "campus__nome")
            .distinct()
        )

        return [(curso.id, curso) for curso in cursos]

    def queryset(self, request, queryset):
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(confirmacao_interesse__inscricao__curso=value)
        return queryset


class AnaliseDocumentalModalidadeListFilter(admin.SimpleListFilter):
    title = "Modalidade"
    parameter_name = "modalidade"

    def lookups(self, request, model_admin):
        modalidades = models.Modalidade.objects.all().order_by("nome")

        filtros = {}

        edicao_id = request.GET.get("edicao")
        if edicao_id and edicao_id.isdigit():
            filtros.update(chamada__etapa__edicao=edicao_id)

        campus_id = request.GET.get("campus")
        if campus_id and campus_id.isdigit():
            filtros.update(chamada__curso__campus=campus_id)

        curso_id = request.GET.get("curso")
        if curso_id and curso_id.isdigit():
            filtros.update(chamada__curso=curso_id)

        modalidades = modalidades.filter(**filtros).distinct()

        return [(m.id, m) for m in modalidades]

    def queryset(self, request, queryset):
        value = self.value()
        if value and value.isdigit():
            return queryset.filter(confirmacao_interesse__inscricao__modalidade=value)
        return queryset


class ConfirmacaoInteresseEtapaListFilter(admin.SimpleListFilter):
    title = "Etapa"
    parameter_name = "etapa"

    def lookups(self, request, model_admin):
        etapas = (
            models.Etapa.objects.filter(confirmacoes_interesse__isnull=False)
            .order_by(
                "edicao__processo_seletivo",
                "-edicao__ano",
                "-edicao__semestre",
                "edicao__nome",
                "numero",
                "campus",
            )
            .distinct()
        )
        return [(etapa.id, etapa) for etapa in etapas]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(inscricao__curso=value)
        return queryset


class ConfirmacaoInteresseCursoListFilter(admin.SimpleListFilter):
    title = "Curso"
    parameter_name = "curso"

    def lookups(self, request, model_admin):
        cursos = (
            CursoSelecao.objects.filter(
                inscricoes_mec__confirmacaointeresse__isnull=False
            )
            .ordena_por_formacao("curso__nome", "modalidade", "turno", "campus__nome")
            .distinct()
        )
        return [(curso.id, curso) for curso in cursos]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(inscricao__curso=value)
        return queryset


class RecursosCursoListFilter(admin.SimpleListFilter):
    title = "Curso"
    parameter_name = "curso"

    def lookups(self, request, model_admin):
        pk_recursos = (
            model_admin.get_queryset(request).distinct().values_list("pk", flat=True)
        )
        cursos = (
            CursoSelecao.objects.filter(
                inscricoes_mec__confirmacaointeresse__analisedocumental__recurso__in=pk_recursos
            )
            .ordena_por_formacao("curso__nome", "modalidade", "turno", "campus__nome")
            .distinct()
        )
        return [(curso.id, curso) for curso in cursos]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(
                analise_documental__confirmacao_interesse__inscricao__curso=value
            )
        return queryset
