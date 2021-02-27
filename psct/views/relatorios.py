from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.urls import reverse
from django.views import generic

from base.custom.datatypes import BreadCrumb
from cursos.models import Campus, CursoSelecao
from psct.forms import relatorios as form
from psct.models import InscricaoPreAnalise
from psct.models import PilhaInscricaoAjuste
from psct.models import SituacaoInscricao


class DashboardView(PermissionRequiredMixin, generic.TemplateView):
    template_name = "psct/relatorios/dashboard.html"
    titulo = "Relatórios do PSCT"
    permission_required = "psct.view_consulta"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = self.titulo
        return data


class DemandaView(PermissionRequiredMixin, generic.FormView):
    form_class = form.DemandaForm
    template_name = "psct/relatorios/demanda.html"
    permission_required = "psct.view_consulta"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formacao = self.request.GET.get("formacao")
        campus = self.request.GET.get("campus")
        processo_inscricao = self.request.GET.get("processo_inscricao")

        filters = dict(processoinscricao__isnull=False)

        if formacao:
            filters["formacao"] = formacao
        if campus:
            filters["campus_id"] = campus
        if processo_inscricao:
            filters["processoinscricao"] = processo_inscricao

        cursos = (
            CursoSelecao.objects.filter(**filters)
            .order_by("campus", "formacao", "curso")
            .distinct()
        )

        context["cursos"] = cursos
        context["processo_inscricao"] = processo_inscricao
        context["titulo"] = "Demanda de Inscrições"
        return context

    def get_initial(self):
        initial = super().get_initial()
        if "formacao" in self.request.GET:
            initial["formacao"] = self.request.GET.get("formacao")
        if "campus" in self.request.GET:
            initial["campus"] = self.request.GET.get("campus")
        if "processo_inscricao" in self.request.GET:
            initial["processo_inscricao"] = self.request.GET.get("processo_inscricao")
        return initial


class AvaliacoesView(PermissionRequiredMixin, generic.FormView):
    form_class = form.EditalForm
    template_name = "psct/relatorios/avaliacoes.html"
    permission_required = "psct.view_consulta"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        edital = self.request.GET.get("edital")
        campi = Campus.objects.filter(
            cursonocampus__processoinscricao__isnull=False
        ).distinct()
        titulo = "Quantitativo de Avaliações"
        context["titulo"] = titulo
        context["campus"] = campi
        resultado = []

        filters = {}

        if edital:
            filters["fase__edital"] = edital
        else:
            filters["fase__edital__ano"] = 2016

        total_sem_avaliacoes = (
            InscricaoPreAnalise.objects.filter(
                **filters, avaliacoes_avaliador__isnull=True
            )
            .distinct()
            .count()
        )
        total_uma_avaliacoes = (
            InscricaoPreAnalise.objects.filter(
                **filters, avaliacoes_avaliador__isnull=False
            )
            .annotate(qtde_avaliacoes=Count("avaliacoes_avaliador"))
            .filter(qtde_avaliacoes=1)
            .distinct()
            .count()
        )
        total_duas_avaliacoes = (
            InscricaoPreAnalise.objects.filter(
                **filters, avaliacoes_avaliador__isnull=False
            )
            .annotate(qtde_avaliacoes=Count("avaliacoes_avaliador"))
            .filter(qtde_avaliacoes__gt=1)
            .distinct()
            .count()
        )
        total_inscritos = (
            InscricaoPreAnalise.objects.filter(**filters).distinct().count()
        )

        total_concluido = 0
        if total_inscritos:
            total_concluido = round(total_duas_avaliacoes / total_inscritos * 100)

        for campus in campi:
            estatistica = {}
            filters["curso__campus"] = campus
            sem_avaliacoes = (
                InscricaoPreAnalise.objects.filter(
                    **filters, avaliacoes_avaliador__isnull=True
                )
                .distinct()
                .count()
            )
            uma_avaliacoes = (
                InscricaoPreAnalise.objects.filter(
                    **filters, avaliacoes_avaliador__isnull=False
                )
                .annotate(qtde_aval=Count("avaliacoes_avaliador"))
                .filter(qtde_aval=1)
                .distinct()
                .count()
            )
            duas_avaliacoes = (
                InscricaoPreAnalise.objects.filter(
                    **filters, avaliacoes_avaliador__isnull=False
                )
                .annotate(qtde_aval=Count("avaliacoes_avaliador"))
                .filter(qtde_aval__gt=1)
                .distinct()
                .count()
            )
            inscritos = InscricaoPreAnalise.objects.filter(**filters).count()

            estatistica["nome"] = campus.nome
            estatistica["sem_avaliacoes"] = sem_avaliacoes
            estatistica["uma_avaliacoes"] = uma_avaliacoes
            estatistica["duas_avaliacoes"] = duas_avaliacoes
            estatistica["inscritos"] = inscritos
            if inscritos:
                estatistica["concluido"] = round(duas_avaliacoes / inscritos * 100)
                resultado.append(estatistica)

        context["resultados"] = resultado

        context["total_sem_avaliacoes"] = total_sem_avaliacoes
        context["total_uma_avaliacoes"] = total_uma_avaliacoes
        context["total_duas_avaliacoes"] = total_duas_avaliacoes
        context["total_inscritos"] = total_inscritos
        context["total_concluido"] = total_concluido

        context["breadcrumb"] = BreadCrumb.create(
            ("Relatórios", reverse("dashboard")), (titulo, "")
        )

        return context

    def get_initial(self):
        initial = super().get_initial()
        if "edital" in self.request.GET:
            initial["edital"] = self.request.GET.get("edital")
        return initial


class AvaliadoresView(PermissionRequiredMixin, generic.FormView):
    form_class = form.EditalForm
    template_name = "psct/relatorios/avaliadores.html"
    permission_required = "psct.view_consulta"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        edital = self.request.GET.get("edital")

        if edital:
            avaliadores = (
                User.objects.filter(
                    avaliacoes_avaliador_psct__isnull=False,
                    avaliacoes_avaliador_psct__inscricao__fase__edital=edital,
                )
                .distinct()
                .annotate(avaliacoes=(Count("avaliacoes_avaliador_psct")))
                .order_by("-avaliacoes")
            )

        else:
            avaliadores = (
                User.objects.filter(avaliacoes_avaliador_psct__isnull=False)
                .distinct()
                .annotate(avaliacoes=(Count("avaliacoes_avaliador_psct")))
                .order_by("-avaliacoes")
            )

        resultado = avaliadores.aggregate(total=Sum("avaliacoes"))
        titulo = "Quantidade de Análises por Avaliador"
        context["titulo"] = titulo
        context["avaliadores"] = avaliadores
        context["total"] = resultado["total"]

        context["breadcrumb"] = BreadCrumb.create(
            ("Relatórios", reverse("dashboard")), (titulo, "")
        )
        return context

    def get_initial(self):
        initial = super().get_initial()
        if "edital" in self.request.GET:
            initial["edital"] = self.request.GET.get("edital")
        return initial


class StatusAvaliacoesView(PermissionRequiredMixin, generic.FormView):
    form_class = form.EditalForm
    template_name = "psct/relatorios/status_avaliacoes.html"
    permission_required = "psct.view_consulta"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        edital = self.request.GET.get("edital")
        campi = Campus.objects.filter(
            cursonocampus__processoinscricao__isnull=False
        ).distinct()
        titulo = "Quantitativo de Avaliações"
        context["titulo"] = titulo
        context["campus"] = campi
        resultado = []

        filters = {}

        if edital:
            filters["fase__edital"] = edital
        else:
            filters["fase__edital__ano"] = 2016

        total_sem_avaliacoes = (
            InscricaoPreAnalise.objects.filter(
                **filters, avaliacoes_avaliador__isnull=True
            )
            .distinct()
            .count()
        )
        total_pendentes = InscricaoPreAnalise.objects.filter(
            **filters, situacao=SituacaoInscricao.AVALIACAO_PENDENTE.name
        ).count()
        total_deferidas = InscricaoPreAnalise.objects.filter(
            **filters, situacao=SituacaoInscricao.DEFERIDA.name
        ).count()
        total_indeferidas = InscricaoPreAnalise.objects.filter(
            **filters, situacao=SituacaoInscricao.INDEFERIDA.name
        ).count()
        total_divergentes = InscricaoPreAnalise.objects.filter(
            **filters, situacao=SituacaoInscricao.AGUARDANDO_HOMOLOGADOR.name
        ).count()
        total_inscritos = InscricaoPreAnalise.objects.filter(**filters).count()

        porcentagem_concluidas = 0
        if total_inscritos:
            porcentagem_concluidas = round(
                (total_deferidas + total_indeferidas) / total_inscritos * 100
            )

        for campus in campi:
            estatistica = {}
            filters["curso__campus"] = campus
            total_sem_avaliacoes = (
                InscricaoPreAnalise.objects.filter(
                    **filters, avaliacoes_avaliador__isnull=True
                )
                .distinct()
                .count()
            )
            pendentes = InscricaoPreAnalise.objects.filter(
                **filters, situacao=SituacaoInscricao.AVALIACAO_PENDENTE.name
            ).count()
            deferidas = InscricaoPreAnalise.objects.filter(
                **filters, situacao=SituacaoInscricao.DEFERIDA.name
            ).count()
            indeferidas = InscricaoPreAnalise.objects.filter(
                **filters, situacao=SituacaoInscricao.INDEFERIDA.name
            ).count()
            divergentes = InscricaoPreAnalise.objects.filter(
                **filters, situacao=SituacaoInscricao.AGUARDANDO_HOMOLOGADOR.name
            ).count()
            inscritos = InscricaoPreAnalise.objects.filter(**filters).count()

            concluidas = deferidas + indeferidas
            porcentagem_concluidas = 0
            if inscritos:
                porcentagem_concluidas = round(concluidas / inscritos * 100)

            estatistica["nome"] = campus.nome
            estatistica["deferidas"] = deferidas
            estatistica["indeferidas"] = indeferidas
            estatistica["pendentes"] = pendentes
            estatistica["divergentes"] = divergentes
            estatistica["inscritos"] = inscritos
            estatistica["concluidas"] = concluidas
            if inscritos:
                estatistica["porcentagem_concluidas"] = porcentagem_concluidas
                resultado.append(estatistica)

        context["resultados"] = resultado

        context["total_sem_avaliacoes"] = total_sem_avaliacoes
        context["total_pendentes"] = total_pendentes
        context["total_deferidas"] = total_deferidas
        context["total_indeferidas"] = total_indeferidas
        context["total_inscritos"] = total_inscritos
        context["total_divergentes"] = total_divergentes
        context["total_concluidas"] = total_deferidas + total_indeferidas
        context["porcentagem_concluidas"] = porcentagem_concluidas

        context["breadcrumb"] = BreadCrumb.create(
            ("Relatórios", reverse("dashboard")), (titulo, "")
        )

        return context

    def get_initial(self):
        initial = super().get_initial()
        if "edital" in self.request.GET:
            initial["edital"] = self.request.GET.get("edital")
        return initial


class AjustesView(PermissionRequiredMixin, generic.FormView):
    form_class = form.EditalForm
    template_name = "psct/relatorios/ajustes_pontuacao.html"
    permission_required = "psct.view_consulta"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        edital = self.request.GET.get("edital")
        campi = Campus.objects.filter(
            cursonocampus__processoinscricao__isnull=False
        ).distinct()
        titulo = "Quantitativo de Ajustes de Pontuacao"
        context["titulo"] = titulo
        context["campus"] = campi
        resultado = []

        filters = {}

        if edital:
            filters["fase__edital"] = edital
            total_inscricoes = PilhaInscricaoAjuste.objects.filter(
                inscricoes__fase__edital=edital
            ).aggregate(total_inscricoes=Count("inscricoes"))
            total_ajustar = total_inscricoes["total_inscricoes"]
        else:
            filters["fase__edital__ano"] = 2016
            total_inscricoes = PilhaInscricaoAjuste.objects.filter(
                inscricoes__fase__edital__ano=2016
            ).aggregate(total_inscricoes=Count("inscricoes"))
            total_ajustar = total_inscricoes["total_inscricoes"]

        total_analisados = (
            InscricaoPreAnalise.objects.filter(
                **filters, pontuacoes_avaliadores__isnull=False
            )
            .distinct()
            .count()
        )
        total_analisados_indeferidos = (
            InscricaoPreAnalise.objects.filter(
                **filters,
                pontuacoes_avaliadores__isnull=False,
                situacao=SituacaoInscricao.INDEFERIDA.name
            )
            .distinct()
            .count()
        )
        total_analisados_deferidos = (
            InscricaoPreAnalise.objects.filter(
                **filters,
                pontuacoes_avaliadores__isnull=False,
                situacao=SituacaoInscricao.DEFERIDA.name
            )
            .distinct()
            .count()
        )
        total_homologados = (
            InscricaoPreAnalise.objects.filter(
                **filters, pontuacoes_homologadores__isnull=False
            )
            .distinct()
            .count()
        )

        for campus in campi:
            filters["curso__campus"] = campus
            analisados = (
                InscricaoPreAnalise.objects.filter(
                    **filters, pontuacoes_avaliadores__isnull=False
                )
                .distinct()
                .count()
            )
            if analisados:
                estatistica = {}
                analisados_indeferidos = (
                    InscricaoPreAnalise.objects.filter(
                        **filters,
                        pontuacoes_avaliadores__isnull=False,
                        situacao=SituacaoInscricao.INDEFERIDA.name
                    )
                    .distinct()
                    .count()
                )
                analisados_deferidos = (
                    InscricaoPreAnalise.objects.filter(
                        **filters,
                        pontuacoes_avaliadores__isnull=False,
                        situacao=SituacaoInscricao.DEFERIDA.name
                    )
                    .distinct()
                    .count()
                )
                homologados = (
                    InscricaoPreAnalise.objects.filter(
                        **filters, pontuacoes_homologadores__isnull=False
                    )
                    .distinct()
                    .count()
                )

                if edital:
                    filters["fase__edital"] = edital
                    inscricoes = PilhaInscricaoAjuste.objects.filter(
                        inscricoes__curso__campus=campus,
                        inscricoes__fase__edital=edital,
                    ).aggregate(total_inscricoes=Count("inscricoes"))
                    ajustar = inscricoes["total_inscricoes"]
                else:
                    filters["fase__edital__ano"] = 2016
                    inscricoes = PilhaInscricaoAjuste.objects.filter(
                        inscricoes__curso__campus=campus,
                        inscricoes__fase__edital__ano=2016,
                    ).aggregate(total_inscricoes=Count("inscricoes"))
                    ajustar = inscricoes["total_inscricoes"]

                estatistica["nome"] = campus.nome
                estatistica["analisados"] = analisados
                estatistica["analisados_indeferidos"] = analisados_indeferidos
                estatistica["analisados_deferidos"] = analisados_deferidos
                estatistica["homologados"] = homologados
                estatistica["ajustar"] = ajustar
                estatistica["pendentes"] = ajustar - analisados

                resultado.append(estatistica)

        context["resultados"] = resultado

        context["analisados"] = total_analisados
        context["analisados_indeferidos"] = total_analisados_indeferidos
        context["analisados_deferidos"] = total_analisados_deferidos
        context["homologados"] = total_homologados
        context["ajustar"] = total_ajustar
        context["pendentes"] = total_ajustar - total_analisados

        context["breadcrumb"] = BreadCrumb.create(
            ("Relatórios", reverse("dashboard")), (titulo, "")
        )

        return context

    def get_initial(self):
        initial = super().get_initial()
        if "edital" in self.request.GET:
            initial["edital"] = self.request.GET.get("edital")
        return initial
