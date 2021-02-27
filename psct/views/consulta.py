from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, redirect
from django.views import generic

from base.custom.views.mixin import GroupRequiredMixin
from cursos.models import Campus, CursoSelecao
from editais.models import Edital
from psct.dashboard import charts, queries
from psct.models.consulta import Consulta, ConsultaMalFormada
from psct.tasks.consulta import generate_xls


class DashboardView(GroupRequiredMixin, generic.TemplateView):
    group_required = "Administradores PSCT"
    template_name = "psct/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        edital, campus, curso = None, None, None
        context["wide"] = True
        context["editais"] = Edital.objects.filter(
            processo_inscricao__isnull=False
        ).order_by("-id")[:10]
        context["campi"] = (
            Campus.objects.filter(cursonocampus__cursoselecao__processoinscricao__isnull=False)
            .distinct()
            .order_by("nome")
        )
        context["cursos"] = CursoSelecao.objects.none()

        params_curso = {"processoinscricao__isnull": False}

        if self.request.GET.get("edital"):
            edital = get_object_or_404(Edital, pk=self.request.GET.get("edital"))
            params_curso["id__in"] = edital.processo_inscricao.cursos.values_list(
                "id", flat=True
            )

        if self.request.GET.get("campus"):
            campus = get_object_or_404(Campus, pk=self.request.GET.get("campus"))
            params_curso["campus"] = campus
            context["cursos"] = CursoSelecao.objects.filter(**params_curso).order_by(
                "curso__nome"
            )

        if self.request.GET.get("curso"):
            curso = get_object_or_404(CursoSelecao, pk=self.request.GET.get("curso"))

        context["edital"] = edital
        context["campus"] = campus
        context["curso"] = curso

        context["chart_aproveitamento_inscricoes"] = charts.AproveitamentoInscricoes(
            edital, campus, curso
        )
        context["chart_andamento_recurso"] = charts.AndamentoRecurso(
            edital, campus, curso
        )
        context[
            "chart_avaliacoes_homologacoes_diarias"
        ] = charts.AvaliacoesHomologacoesDiarias(edital, campus, curso)

        context["total_inscricoes_concluidas"] = queries.get_inscricoes_concluidas(
            edital, campus, curso
        ).count()
        context["total_inscricoes_analisadas"] = queries.get_inscricoes_analisadas(
            edital, campus, curso
        ).count()
        context["conclusao_analise"] = queries.get_percentual_conclusao_analise(
            edital, campus, curso
        )
        context["total_inscricoes_deferidas"] = queries.get_inscricoes_deferidas(
            edital, campus, curso
        ).count()
        context["total_inscricoes_indeferidas"] = queries.get_inscricoes_indeferidas(
            edital, campus, curso
        ).count()
        context["total_inscricoes_homologadas"] = queries.get_inscricoes_homologadas(
            edital, campus, curso
        ).count()
        context["total_homologacoes"] = queries.get_homologacoes(
            edital, campus, curso
        ).count()
        context[
            "total_inscricoes_sem_avaliadores"
        ] = queries.get_inscricoes_sem_avaliadores(edital, campus, curso).count()

        context["melhores_avaliadores"] = queries.get_melhores_avaliadores(
            edital, campus, curso
        )
        context["piores_avaliadores"] = queries.get_avaliacoes_pendentes_a_mais_tempo(
            edital, campus, curso
        )

        return context


class ConsultaPermission(PermissionRequiredMixin):
    login_url = "/login"
    raise_exception = True
    permission_required = "psct.view_consulta"

    def has_permission(self):
        perm = super().has_permission()
        self.consulta = get_object_or_404(Consulta, pk=self.kwargs["pk"])
        if perm:
            if self.consulta.compartilhar:
                return True
            elif self.consulta.user == self.request.user:
                return True
        return False


class ViewConsulta(ConsultaPermission, generic.DetailView):
    model = Consulta
    template_name = "psct/consulta/consulta_detail.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        try:
            queryset = self.object.consulta_queryset
            data["total"] = queryset.count()
            paginator = Paginator(
                self.object.consulta_queryset, self.object.itens_por_pagina
            )
            page_n = self.request.GET.get("page", 1)
            try:
                page = paginator.page(page_n)
            except PageNotAnInteger:
                page = paginator.page(1)
            except EmptyPage:
                page = paginator.page(paginator.num_pages)
            data["queryset"] = page
        except ConsultaMalFormada:
            messages.error(
                self.request,
                "Erro: Sua consulta contém um erro e não é possível executá-la",
            )

        return data

    def post(self, request, *args, **kwargs):
        generate_xls.delay(request.user.id, self.kwargs["pk"])
        messages.info(
            self.request,
            "Solicitação realizada com sucesso! Você receberá o arquivo em seu email.",
        )
        return redirect("visualizar_consulta_psct", pk=self.kwargs["pk"])
