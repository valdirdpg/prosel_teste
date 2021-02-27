import json
from datetime import date
from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, User
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from django.http import HttpResponse
from django.shortcuts import render
from ifpb_django_permissions.perms import in_any_groups
from reversion.views import RevisionMixin
from base.custom.autocomplete import auto_complete
from base.custom.datatypes import BreadCrumb
from base.custom.views import ListView
from base.custom.views.decorators import column, menu, tab
from base.custom.views.mixin import AnyGroupRequiredMixin, GroupRequiredMixin
from base.pdf import PdfReport, PDFResponse
from base.permissions import AdministradoresSistemicos
from cursos.models import Campus, CursoSelecao
from editais.models import Edital
from monitoring.models import Job
from noticias.models import Noticia
from processoseletivo import filters, pdf
from base.configs import PortalConfig
from . import forms
from . import models
from . import permissions
from . import tasks

class AcessibilidadeView(generic.TemplateView):
    template_name = "base/acessibilidade.html"

class ProcessosIndexView(generic.TemplateView):
    template_name = "processoseletivo/index.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        processo_pk = PortalConfig.PROCESSOPK #int(self.kwargs["processo_pk"])
        processo = get_object_or_404(models.ProcessoSeletivo, pk=processo_pk)
        context["processo"] = processo
        # Lista as ultimas 7 edições de um processo seletivo
        context["ultimas_edicoes"] = models.Edicao.objects.filter(
            processo_seletivo=processo
        ).order_by("id","-ano", "-semestre", "nome")[:7]
        # Lista as ultimas 5 noticias de um processo seletivo
        palavra_chave = processo.palavra_chave
        noticias = Noticia.objects.filter(palavras_chave=palavra_chave)[:5]
        context["noticias"] = noticias
        return context
class ProcessosView(generic.TemplateView):
    template_name = "processoseletivo/index2.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        processo_pk = PortalConfig.PROCESSOPK #int(self.kwargs["processo_pk"])
        processo = get_object_or_404(models.ProcessoSeletivo, pk=processo_pk)
        context["processo"] = processo
        # Lista as ultimas 7 edições de um processo seletivo
        context["ultimas_edicoes"] = models.Edicao.objects.filter(
            processo_seletivo=processo
        ).order_by("id","-ano", "-semestre", "nome")[:7]
        # Lista as ultimas 5 noticias de um processo seletivo
        palavra_chave = processo.palavra_chave
        noticias = Noticia.objects.filter(palavras_chave=palavra_chave)[:5]
        context["noticias"] = noticias
        return context
class EdicoesView(generic.TemplateView):
    template_name = "processoseletivo/edicoes.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        processo_pk = PortalConfig.PROCESSOPK  #int(self.kwargs["processo_pk"])
        processo = get_object_or_404(models.ProcessoSeletivo, pk=processo_pk)
        context["processo"] = processo
        context["edicoes_abertas"] = models.Edicao.objects.filter(
            processo_seletivo=processo, status="ABERTO"
        ).order_by("-ano", "-semestre", "nome")
        edicoes_encerradas = models.Edicao.objects.filter(
            processo_seletivo=processo, status="FECHADO"
        ).order_by("-ano", "-semestre", "nome")
        if edicoes_encerradas.count() <= 10:
            context["edicoes_encerradas"] = edicoes_encerradas
        else:
            paginator = Paginator(
                edicoes_encerradas, 10
            )  # Mostra 10 editais por página
            page_n = self.request.GET.get("page", 1)
            try:
                page = paginator.page(page_n)
            except PageNotAnInteger:
                page = paginator.page(1)
            except EmptyPage:
                page = paginator.page(paginator.num_pages)
            context["edicoes_encerradas"] = page
            context["paginado"] = "S"
        return context
class EdicaoView(generic.TemplateView):
    template_name = "processoseletivo/edicao.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        processo_pk = int(self.kwargs["processo_pk"])
        processo = get_object_or_404(models.ProcessoSeletivo, pk=processo_pk)
        context["processo"] = processo
        edicao_pk = int(self.kwargs["edicao_pk"])
        edicao = get_object_or_404(models.Edicao, pk=edicao_pk)
        context["edicao"] = edicao
        if Edital.objects.filter(
            edicao=edicao, tipo="ABERTURA", publicado=True
        ).exists():
            edital = Edital.objects.filter(
                edicao=edicao, tipo="ABERTURA", publicado=True
            ).first()
            context["edital"] = edital
            context["exibe_prazo"] = edital.niveis_selecao.exclude(
                valor_inscricao=0
            ).exists()
        etapas_resultado = edicao.etapa_set.filter(numero=0)
        context["etapa_resultado_unica"] = (
            etapas_resultado.first() if etapas_resultado.count() == 1 else None
        )
        context["etapa_resultado_andamento"] = etapas_resultado.filter(
            encerrada=False
        ).exists()
        context["etapas_resultado_publicadas"] = (
            etapas_resultado.exists()
            and not etapas_resultado.filter(publica=False).exists()
        )
        etapas_espera = edicao.etapa_set.filter(publica=True, numero__gt=0)
        campi = (
            etapas_espera.values_list("campus__id", "campus__nome")
            .order_by("campus")
            .distinct()
        )
        etapa_campus = dict()
        for (id, nome) in campi:
            etapa_campus[nome] = etapas_espera.filter(campus__id=id).order_by("numero")
        context["etapa_espera_campus"] = etapa_campus
        return context
class CampusView(generic.TemplateView):
    template_name = "processoseletivo/campus.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        edicao_pk = kwargs.get("edicao_pk")
        edicao = get_object_or_404(models.Edicao, pk=edicao_pk)
        etapa_pk = kwargs.get("etapa_pk")
        if etapa_pk:
            etapa = get_object_or_404(models.Etapa, pk=etapa_pk)
        else:
            etapa = edicao.etapa_set.last()
        context["etapa"] = etapa
        context["campi_etapa"] = [
            models.CampusEtapa(c, etapa) for c in Campus.objects.all().order_by("nome")
        ]
        filter_vagas = {"etapa": etapa}
        if etapa.campus:
            filter_vagas.update({"curso__campus": etapa.campus})
        context["has_vagas"] = models.Chamada.objects.filter(**filter_vagas).exists()
        context["tipo_tabela_dados"] = "Unidades de Ensino:"
        context["admin_permission"] = in_any_groups(
            self.request.user,
            [permissions.AdministradoresdeChamadasporCampi, AdministradoresSistemicos],
        )
        complemento = " da Lista de Espera" if not etapa.is_resultado else ""
        context["breadcrumb"] = BreadCrumb.create(
            ("Processos Seletivos", reverse("indexprocessoseletivo")),
            (
                f"{edicao.processo_seletivo.sigla}",
                reverse("processoseletivo", args=[edicao.processo_seletivo.id]),
            ),
            ("Edições", reverse("edicoes", args=[edicao.processo_seletivo.id])),
            (
                f"{edicao}",
                reverse("edicao", args=[edicao.processo_seletivo.id, edicao.id]),
            ),
            (f"{etapa.label}{complemento}", ""),
        )
        return context
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        etapa = context["etapa"]
        if etapa.campus:
            return redirect(reverse("cursos", args=[etapa.pk, etapa.campus.id]))
        return self.render_to_response(context)
class EtapasView(generic.TemplateView):
    template_name = "processoseletivo/etapas.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "edicao_pk" in self.kwargs:
            pk = int(self.kwargs["edicao_pk"])
            edicao = get_object_or_404(models.Edicao, pk=pk)
            context["edicao"] = edicao
            context["processo"] = edicao.processo_seletivo
            etapas = models.Etapa.objects.filter(edicao=edicao, publica=True).order_by(
                Coalesce("numero", "edicao").desc()
            )
        elif "processo_pk" in self.kwargs:
            processo_id = int(self.kwargs["processo_pk"])
            context["processo"] = get_object_or_404(
                models.ProcessoSeletivo, pk=processo_id
            )
            etapas = models.Etapa.objects.filter(
                edicao__processo_seletivo=processo_id, publica=True
            ).order_by(Coalesce("numero", "edicao").desc())
        else:
            etapas = models.Etapa.objects.none()
        if etapas.count() <= 10:
            context["etapas"] = etapas
        else:
            paginator = Paginator(etapas, 10)
            page_n = self.request.GET.get("page", 1)
            try:
                page = paginator.page(page_n)
            except PageNotAnInteger:
                page = paginator.page(1)
            except EmptyPage:
                page = paginator.page(paginator.num_pages)
            context["etapas"] = page
            context["paginado"] = "S"
        return context
class EtapasResultadoView(generic.TemplateView):
    template_name = "processoseletivo/etapas_resultado.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = int(kwargs["edicao_pk"])
        edicao = get_object_or_404(models.Edicao, pk=pk)
        context["edicao"] = edicao
        etapas = edicao.etapa_set.filter(numero=0)
        context["etapas"] = etapas
        context["etapa_publicada"] = not etapas.filter(publica=False).exists()
        context["admin_permission"] = in_any_groups(
            self.request.user,
            [permissions.AdministradoresdeChamadasporCampi, AdministradoresSistemicos],
        )
        breadcrumb = BreadCrumb.create(
            ("Processos Seletivos", reverse("indexprocessoseletivo")),
            (
                f"{edicao.processo_seletivo.sigla}",
                reverse("processoseletivo", args=[edicao.processo_seletivo.id]),
            ),
            ("Edições", reverse("edicoes", args=[edicao.processo_seletivo.id])),
            (
                f"{edicao}",
                reverse("edicao", args=[edicao.processo_seletivo.id, edicao.id]),
            ),
            ("Etapa de Resultado", ""),
        )
        context["breadcrumb"] = breadcrumb
        return context
class CursosView(generic.TemplateView):
    template_name = "processoseletivo/cursos.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campus = get_object_or_404(Campus, pk=kwargs["campus"])
        etapa = get_object_or_404(models.Etapa, pk=kwargs["pk"])
        edicao = etapa.edicao
        cursos = CursoSelecao.objects.filter(
            chamada__curso__campus=campus, chamada__etapa=etapa
        ).distinct()
        context["campus"] = campus
        context["etapa"] = etapa
        context["cursos_etapa"] = [models.CursoEtapa(c, etapa) for c in cursos]
        context["has_vagas"] = models.Chamada.objects.filter(
            etapa=etapa, curso__campus=campus
        ).exists()
        context["tipo_tabela_dados"] = "Cursos:"
        context["admin_permission"] = in_any_groups(
            self.request.user,
            [permissions.AdministradoresdeChamadasporCampi, AdministradoresSistemicos],
        )
        breadcrumb = BreadCrumb.create(
            ("Processos Seletivos", reverse("indexprocessoseletivo")),
            (
                f"{edicao.processo_seletivo.sigla}",
                reverse("processoseletivo", args=[edicao.processo_seletivo.id]),
            ),
            ("Edições", reverse("edicoes", args=[edicao.processo_seletivo.id])),
            (
                f"{edicao}",
                reverse("edicao", args=[edicao.processo_seletivo.id, edicao.id]),
            ),
        )
        complemento = " da Lista de Espera" if not etapa.is_resultado else ""
        if etapa.campus:
            breadcrumb.add(
                f"{etapa.label}{complemento} - {etapa.campus}",
                reverse("edicao_etapa", args=[edicao.id, etapa.pk]),
            )
        else:
            breadcrumb.add_many(
                [
                    (
                        f"{etapa.label}{complemento}",
                        reverse("edicao_etapa", args=[edicao.id, etapa.pk]),
                    ),
                    (f"{campus}", ""),
                ]
            )
        context["breadcrumb"] = breadcrumb
        return context
class ChamadaView(generic.TemplateView):
    template_name = "processoseletivo/chamada_curso.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campus = get_object_or_404(Campus, pk=kwargs["campus"])
        etapa = get_object_or_404(models.Etapa, pk=kwargs["pk"])
        edicao = etapa.edicao
        curso = get_object_or_404(CursoSelecao, pk=kwargs["curso"])
        context["campus"] = campus
        context["etapa"] = etapa
        context["curso"] = curso
        chamadas = models.Chamada.objects.filter(etapa=etapa, curso=curso).order_by(
            "modalidade"
        )
        context["chamadas"] = chamadas
        context["has_vagas"] = chamadas.exists()
        context["tipo_tabela_dados"] = "Candidatos convocados:"
        context["admin_permission"] = in_any_groups(
            self.request.user,
            [permissions.AdministradoresdeChamadasporCampi, AdministradoresSistemicos],
        )
        complemento = " da Lista de Espera" if not etapa.is_resultado else ""
        context["breadcrumb"] = BreadCrumb.create(
            ("Processos Seletivos", reverse("indexprocessoseletivo")),
            (
                f"{edicao.processo_seletivo.sigla}",
                reverse("processoseletivo", args=[edicao.processo_seletivo.id]),
            ),
            ("Edições", reverse("edicoes", args=[edicao.processo_seletivo.id])),
            (
                f"{edicao}",
                reverse("edicao", args=[edicao.processo_seletivo.id, edicao.id]),
            ),
            (
                f"{etapa.label}{complemento}",
                reverse("edicao_etapa", args=[edicao.id, etapa.pk]),
            ),
            (f"{campus}", reverse("cursos", args=[etapa.pk, campus.id])),
            (f"{curso.nome} ({curso.get_turno_display()})", ""),
        )
        return context
class ImportacaoView(GroupRequiredMixin, generic.FormView):
    login_url = "/admin/login/"
    group_required = models.GRUPO_SISTEMICO
    form_class = forms.ImportacaoForm
    template_name = "processoseletivo/importacao.html"
    raise_exception = True
    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.edicao = get_object_or_404(models.Edicao, pk=self.kwargs["pk"])
            if self.edicao.pode_importar:
                self.modalidades = self.edicao.get_modalidades_para_importacao()
            else:
                return False
        return perm
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = f"Importar dados do {self.edicao}"
        data["nome_botao"] = "Sim"
        data["modalidades"] = self.modalidades
        data["breadcrumb"] = BreadCrumb.create(
            ("Admin", reverse("admin:index")),
            ("Processo Seletivo", reverse("admin:app_list", args=["processoseletivo"])),
            (
                "Edição",
                reverse(
                    "admin:processoseletivo_edicao_change", args=[self.kwargs["pk"]]
                ),
            ),
            ("Importar dados", ""),
        )
        return data
    def form_valid(self, form):
        form.save()
        async_result = tasks.importar_csv.delay(self.kwargs["pk"], self.request.user.id)
        self.job = Job.new(
            self.request.user, async_result, name=tasks.importar_csv.name
        )
        return super().form_valid(form)
    def get_success_url(self):
        messages.info(self.request, "Esta operação irá demorar alguns minutos.")
        return self.job.get_absolute_url()
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["modalidades"] = self.modalidades
        return kwargs
class CreateChamadaView(AnyGroupRequiredMixin, generic.View):
    group_required = [models.GRUPO_CAMPI, models.GRUPO_SISTEMICO]
    raise_exception = True
    login_url = "/admin/login/"
    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.etapa = get_object_or_404(models.Etapa, pk=self.kwargs["etapa_pk"])
            if models.is_admin_campus(self.request.user):
                return self.etapa.campus in self.request.user.lotacoes.all()
        return perm
    def get(self, request, *args, **kwargs):
        if self.etapa.encerrada:
            messages.info(
                request, "Você não pode gerar chamadas para uma etapa encerrada"
            )
            return redirect(
                "admin:processoseletivo_etapa_change", self.kwargs["etapa_pk"]
            )
        if self.etapa.chamadas.exists():
            messages.error(request, "Já existem chamadas definidas")
            return redirect(
                "admin:processoseletivo_etapa_change", self.kwargs["etapa_pk"]
            )
        messages.info(
            request,
            "Esta operação irá demorar vários minutos, você receberá um email quando ela estiver concluída",
        )
        tasks.gerar_chamada_ps.delay(self.kwargs["etapa_pk"], request.user.id)
        return redirect("admin:processoseletivo_etapa_change", self.kwargs["etapa_pk"])
class AddCandidatosView(AnyGroupRequiredMixin, generic.View):
    group_required = [models.GRUPO_CAMPI, models.GRUPO_SISTEMICO]
    raise_exception = True
    login_url = "/admin/login/"
    def has_permission(self):
        perm = super().has_permission()
        chamada = get_object_or_404(models.Chamada, pk=self.kwargs["chamada_pk"])
        if chamada.etapa.is_resultado:
            return False
        if perm:
            if models.is_admin_campus(self.request.user):
                return chamada.etapa.campus in self.request.user.lotacoes.all()
        return perm
    def dispatch(self, request, *args, **kwargs):
        chamada = get_object_or_404(models.Chamada, pk=self.kwargs["chamada_pk"])
        if models.ConfirmacaoInteresse.objects.filter(
            inscricao__chamada=chamada
        ).exists():
            messages.warning(
                request,
                "Não é permitido adicionar candidatos a uma chamada que possui "
                "confirmações de interesse cadastradas.",
            )
            return redirect(
                reverse("admin:processoseletivo_chamada_change", args=[chamada.pk])
            )
        return super().dispatch(request, *args, **kwargs)
    def post(self, request, *args, **kwargs):
        chamada = models.Chamada.objects.get(pk=self.kwargs["chamada_pk"])
        chamada.adicionar_inscricoes()
        messages.info(request, "Candidatos adicionados com sucesso")
        return redirect(
            "admin:processoseletivo_chamada_change", self.kwargs["chamada_pk"]
        )
class AjaxView(AnyGroupRequiredMixin, generic.View):
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI]
    raise_exception = True
    login_url = "/admin/login/"
    exception = None
    def post(self, request, *args, **kwargs):
        response_data = {"ok": True}
        self.candidato = get_object_or_404(
            models.Candidato, pk=self.kwargs["candidato_pk"]
        )
        self.modalidade = get_object_or_404(
            models.Modalidade, pk=self.kwargs["modalidade_pk"]
        )
        self.etapa = get_object_or_404(models.Etapa, pk=self.kwargs["etapa_pk"])
        self.inscricao = get_object_or_404(
            models.Inscricao,
            candidato=self.candidato,
            edicao=self.etapa.edicao,
            modalidade=self.modalidade,
        )
        try:
            self.do_action()
        except self.exception as e:
            response_data = {"error": e.args}
        return HttpResponse(
            content=json.dumps(response_data),
            status=200,
            content_type="application/json",
        )
    def do_action(self):
        raise NotImplementedError()
class ConfirmarInteresseView(AjaxView):
    exception = models.ConfirmacaoInteresse.Error
    def do_action(self):
        self.inscricao.confirmar_interesse(self.etapa)
class CancelarConfirmacaoView(AjaxView):
    exception = models.ConfirmacaoInteresse.Error
    def do_action(self):
        self.inscricao.cancelar_interesse(self.etapa)
class MatricularView(AjaxView):
    exception = models.Matricula.Error
    def do_action(self):
        self.inscricao.matricular(self.etapa)
class CancelarMatriculaView(AjaxView):
    exception = models.Matricula.Error
    def do_action(self):
        self.inscricao.cancelar_matricula(self.etapa)
class RelatorioConvocadosView(AnyGroupRequiredMixin, generic.View):
    raise_exception = True
    login_url = "/admin/login/"
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI]
    def get(self, request, *args, **kwargs):
        messages.info(
            request,
            "Sua solicitação está sendo processada. Você receberá o arquivo em seu email.",
        )
        tasks.relatorio_convocados_xlsx.delay(self.kwargs["etapa_pk"], request.user.id)
        return redirect("admin:processoseletivo_etapa_change", self.kwargs["etapa_pk"])
class RelatorioConvocadosPorCotaView(AnyGroupRequiredMixin, generic.View):
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI]
    login_url = "/admin/login/"
    raise_exception = True
    def get(self, request, *args, **kwargs):
        messages.info(
            request,
            "Sua solicitação está sendo processada. Você receberá o arquivo em seu e-mail.",
        )
        tasks.relatorio_convocados_por_cota_pdf.delay(
            self.kwargs["etapa_pk"], request.user.id
        )
        return redirect("admin:processoseletivo_etapa_change", self.kwargs["etapa_pk"])
class RelatorioMatriculadosView(AnyGroupRequiredMixin, generic.View):
    raise_exception = True
    login_url = "/admin/login/"
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI]
    def get(self, request, *args, **kwargs):
        messages.info(
            request,
            "Sua solicitação está sendo processada. Você receberá o arquivo em seu email.",
        )
        tasks.relatorio_matriculados_xlsx.delay(
            self.kwargs["etapa_pk"], request.user.id
        )
        return redirect("admin:processoseletivo_etapa_change", self.kwargs["etapa_pk"])
class AnaliseDocumentoEtapaView(AnyGroupRequiredMixin, generic.View):
    raise_exception = True
    login_url = "/admin/login/"
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI]
    def get(self, request, *args, **kwargs):
        messages.info(
            request,
            "Sua solicitação está sendo processada. Você receberá o arquivo em seu email.",
        )
        tasks.analise_documental_etapa_pdf.delay(
            self.kwargs["etapa_pk"], request.user.id
        )
        return redirect("admin:processoseletivo_etapa_change", self.kwargs["etapa_pk"])
class ListagemFinalView(GroupRequiredMixin, generic.View):
    raise_exception = True
    login_url = "/admin/login/"
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI]
    def has_permission(self):
        perm = super().has_permission()
        if perm:
            etapa = get_object_or_404(models.Etapa, pk=self.kwargs["etapa_pk"])
            return etapa.encerrada
        return False
    def get_relatorio(self):
        raise NotImplementedError(
            "É necessário implementar o método get_relatorio com o tipo de relatório a ser gerado."
        )
    def get(self, request, *args, **kwargs):
        messages.info(
            request,
            "Sua solicitação está sendo processada. Você receberá o arquivo em seu email.",
        )
        self.get_relatorio().delay(self.kwargs["etapa_pk"], request.user.id)
        return redirect("admin:processoseletivo_etapa_change", self.kwargs["etapa_pk"])
class ListagemFinalDeferidos(ListagemFinalView):
    def get_relatorio(self):
        return tasks.gerar_listagem_final_deferidos_pdf
class ListagemFinalIndeferidos(ListagemFinalView):
    def get_relatorio(self):
        return tasks.gerar_listagem_final_indeferidos_pdf
class ListagemFinalExcedentes(ListagemFinalView):
    def get_relatorio(self):
        return tasks.gerar_listagem_final_excedentes_pdf
class EncerrarEtapalView(GroupRequiredMixin, generic.View):
    raise_exception = True
    login_url = "/admin/login/"
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI]
    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.etapa = get_object_or_404(models.Etapa, pk=self.kwargs["etapa_pk"])
            return not self.etapa.encerrada
        return False
    def get(self, request, *args, **kwargs):
        if not self.etapa.pode_encerrar():
            messages.error(
                request,
                "A etapa não pode ser encerrada pois existem confirmações de interesse que não foram analisadas.",
            )
            return redirect(
                "admin:processoseletivo_etapa_change", self.kwargs["etapa_pk"]
            )
        messages.info(
            request, "Sua solicitação está sendo processada. Aguarde alguns instantes."
        )
        async_result = tasks.encerrar_etapa.delay(self.kwargs["etapa_pk"])
        job = Job.new(self.request.user, async_result, name=tasks.encerrar_etapa.name)
        return redirect(job.get_absolute_url())
class ReabrirEtapalView(GroupRequiredMixin, generic.View):
    raise_exception = True
    login_url = "/admin/login/"
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI]
    def has_permission(self):
        perm = super().has_permission()
        if perm:
            etapa = get_object_or_404(models.Etapa, pk=self.kwargs["etapa_pk"])
            return etapa.encerrada
        return False
    def get(self, request, *args, **kwargs):
        messages.info(
            request, "Sua solicitação está sendo processada. Aguarde alguns instantes."
        )
        async_result = tasks.reabrir_etapa.delay(self.kwargs["etapa_pk"])
        job = Job.new(self.request.user, async_result, name=tasks.reabrir_etapa.name)
        return redirect(job.get_absolute_url())
class FormulariosAnaliseDocumentoView(GroupRequiredMixin, generic.View):
    raise_exception = True
    login_url = "/admin/login/"
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI]
    def get(self, request, *args, **kwargs):
        chamada = get_object_or_404(models.Chamada, pk=self.kwargs["chamada_pk"])
        if chamada.inscricoes.filter(confirmacaointeresse__isnull=False).exists():
            messages.info(
                request,
                "Sua solicitação está sendo processada. Você receberá o arquivo em seu email.",
            )
            tasks.formulario_analise_documental_pdf.delay(
                self.kwargs["chamada_pk"], request.user.id
            )
        else:
            messages.error(
                request,
                "Os formulários não podem ser gerados pois não há confirmações de interesse para esta chamada.",
            )
        return redirect(
            "admin:processoseletivo_chamada_change", self.kwargs["chamada_pk"]
        )
class VagasView(GroupRequiredMixin, generic.TemplateView):
    raise_exception = True
    login_url = "/admin/login/"
    group_required = "Administradores Sistêmicos"
    template_name = "processoseletivo/vagas.html"
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        edicao = get_object_or_404(models.Edicao, pk=self.kwargs["pk"])
        data["edicao"] = edicao
        data["breadcrumb"] = BreadCrumb.create(
            ("Admin", reverse("admin:index")),
            ("Processo Seletivo", reverse("admin:app_list", args=["processoseletivo"])),
            (
                "Edição",
                reverse(
                    "admin:processoseletivo_edicao_change", args=[self.kwargs["pk"]]
                ),
            ),
            ("Vagas", ""),
        )
        cursos = []
        data["total_vagas"] = models.Vaga.objects.filter(edicao=edicao).count()
        for curso in CursoSelecao.objects.filter(
            inscricoes_mec__edicao=edicao
        ).distinct():
            curso_data = []
            for modalidade in models.Modalidade.objects.all():
                vagas = models.Vaga.objects.filter(
                    edicao=edicao, curso=curso, modalidade=modalidade
                ).count()
                mod = modalidade.resumo if modalidade.resumo else modalidade.nome
                curso_data.append([mod, vagas])
            cursos.append([curso, curso_data])
        data["cursos"] = cursos
        return data
class RelatorioResultadoView(GroupRequiredMixin, generic.View):
    raise_exception = True
    login_url = "/admin/login/"
    group_required = models.GRUPO_SISTEMICO
    def get(self, request, *args, **kwargs):
        messages.info(
            request,
            "Sua solicitação está sendo processada. Você receberá o arquivo em seu email.",
        )
        tasks.relatorio_resultado_csv.delay(self.kwargs["pk"], request.user.id)
        return redirect("admin:processoseletivo_edicao_change", self.kwargs["pk"])
class ReplicarAnaliseDocumentalView(GroupRequiredMixin, generic.FormView):
    group_required = [models.GRUPO_CAMPI, models.GRUPO_SISTEMICO]
    raise_exception = True
    template_name = "reuse/confirmacao.html"
    form_class = forms.BForm
    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.analise_indeferida = get_object_or_404(
                models.AnaliseDocumental, pk=self.kwargs.get("analise_pk")
            )
        return perm
    @transaction.atomic
    def replicar_analise(self):
        inscricao_ampla = self.analise_indeferida.inscricoes_convocacoes_concomitantes().get(
            modalidade=models.ModalidadeEnum.ampla_concorrencia
        )
        etapa = self.analise_indeferida.confirmacao_interesse.etapa
        if models.AnaliseDocumental.objects.filter(
            confirmacao_interesse__inscricao=inscricao_ampla,
            confirmacao_interesse__etapa=etapa,
        ).exists():
            raise models.AnaliseDocumental.AlreadyExists(
                "Não é possível recriar um objeto já existente."
            )
        confirmacao_ampla = models.ConfirmacaoInteresse.objects.create(
            inscricao=inscricao_ampla, etapa=etapa
        )
        self.analise_ampla = models.AnaliseDocumental.objects.create(
            confirmacao_interesse=confirmacao_ampla,
            servidor_coordenacao=self.analise_indeferida.servidor_coordenacao,
            observacao=self.analise_indeferida.observacao,
            data=self.analise_indeferida.data,
            situacao_final=True,
        )
        avaliacoes_ampla = self.analise_indeferida.analise_documental.filter(
            tipo_analise__modalidade=models.ModalidadeEnum.ampla_concorrencia
        ).distinct()
        for avaliacao in avaliacoes_ampla:
            models.AvaliacaoDocumental.objects.create(
                tipo_analise=avaliacao.tipo_analise,
                servidor_setor=avaliacao.servidor_setor,
                analise_documental=self.analise_ampla,
                data=avaliacao.data,
                observacao=avaliacao.observacao,
                situacao=avaliacao.situacao,
            )
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["back_url"] = reverse(
            "admin:processoseletivo_analisedocumental_change",
            args=[self.analise_indeferida.pk],
        )
        data["titulo"] = (
            f"Deseja replicar a análise de documentos do(a) candidato(a) "
            f"{self.analise_indeferida.confirmacao_interesse.inscricao.candidato} e criar a análise de Ampla Concorrência?"
        )
        data["breadcrumb"] = BreadCrumb.create(
            ("Admin", reverse("admin:index")),
            (
                "Processos Seletivos",
                reverse("admin:app_list", args=["processoseletivo"]),
            ),
            (
                "Análises de Documentos",
                reverse("admin:processoseletivo_analisedocumental_changelist"),
            ),
            (
                f"Replicar Análise Documental de {self.analise_indeferida.confirmacao_interesse.inscricao.candidato}",
                "",
            ),
        )
        return data
    def form_valid(self, form):
        try:
            self.replicar_analise()
            self.success_url = reverse(
                "admin:processoseletivo_analisedocumental_change",
                args=[self.analise_ampla.pk],
            )
            messages.info(self.request, "Análise Documental criada com sucesso.")
        except models.AnaliseDocumental.AlreadyExists:
            messages.error(
                self.request, "Análise de documentos de ampla concorrência já existe."
            )
        except models.Inscricao.DoesNotExist:
            messages.error(
                self.request,
                "Não há convocação de ampla concorrência para este candidato.",
            )
        return super().form_valid(form)
    def get_success_url(self):
        if not self.success_url:
            self.success_url = reverse(
                "admin:processoseletivo_analisedocumental_change",
                args=[self.analise_indeferida.pk],
            )
        return super().get_success_url()
class AvaliacaoDocumentalListView(GroupRequiredMixin, ListView):
    template_name = "reuse/listview.html"
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI]
    raise_exception = True
    simple_filters = [
        filters.EdicaoConfirmacaoInteresseFilter,
        filters.CampusConfirmacaoInteresseFilter,
    ]
    list_display = ("candidato", "campus", "edicao", "situacao", "acoes")
    tabs = ["nao_avaliadas", "minhas_avaliacoes", "avaliadas"]
    autocomplete_fields = [
        auto_complete(
            "base.pessoafisica",
            "inscricao__candidato__pessoa",
            ["nome", "cpf", "user__username"],
            "Candidato",
        )
    ]
    model = models.ConfirmacaoInteresse
    ordering = ["inscricao__candidato__pessoa__nome"]
    profile_checker = [
        ("medico", models.GRUPO_MEDICOS),
        ("caest", models.GRUPO_CAEST),
        ("coordenador", models.GRUPO_CAMPI),
        ("administrador", models.GRUPO_SISTEMICO),
    ]
    tipo_analise = None
    add_url = None
    change_url = None
    delete_url = None
    detail_url = None
    titulo = None
    @column("Campus")
    def campus(self, obj):
        return f"{obj.inscricao.curso.campus.nome}"
    @column("Candidato")
    def candidato(self, obj):
        return obj.inscricao.candidato.pessoa
    @column("Edição")
    def edicao(self, obj):
        return obj.inscricao.edicao
    @column("Situação", mark_safe=True)
    def situacao(self, obj: models.ConfirmacaoInteresse):
        analise = models.AnaliseDocumental.objects.filter(
            confirmacao_interesse=obj
        ).first()
        if analise:
            avaliacao = analise.analise_documental.filter(
                tipo_analise__nome=self.tipo_analise
            ).first()
            if avaliacao:
                if avaliacao.situacao:
                    return '<span class="status status-deferido">Deferido</span>'
                else:
                    return '<span class="status status-indeferido">Indeferido</span>'
        return '<span class="status status-pendente">Aguardando Avaliação</span>'
    @menu("Opções", col="Ações")
    def acoes(
        self, menu_obj: ListView.menu_class, obj: models.ConfirmacaoInteresse
    ) -> None:
        pode_avaliar = not obj.etapa.encerrada and obj.etapa.estah_em_periodo_analise()
        avaliacao = models.AvaliacaoDocumental.objects.filter(
            tipo_analise__nome=self.tipo_analise,
            analise_documental__confirmacao_interesse=obj,
        ).first()
        if not avaliacao and pode_avaliar and self.add_url:
            menu_obj.add(
                "Avaliar",
                reverse(self.add_url, kwargs=dict(inscricao_pk=obj.inscricao.pk)),
            )
        elif avaliacao:
            user = f"{self.request.user.get_full_name()} ({self.request.user})"
            if avaliacao.servidor_setor == user:
                if self.change_url and avaliacao.pode_editar():
                    menu_obj.add(
                        "Editar", reverse(self.change_url, kwargs=dict(pk=avaliacao.pk))
                    )
                if self.delete_url and avaliacao.pode_excluir():
                    menu_obj.add(
                        "Excluir",
                        reverse(self.delete_url, kwargs=dict(pk=avaliacao.pk)),
                    )
            if self.detail_url:
                menu_obj.add(
                    "Visualizar", reverse(self.detail_url, kwargs=dict(pk=avaliacao.pk))
                )
        else:
            menu_obj.add("Nenhuma ação disponível", "")
    @tab(name="Não avaliadas")
    def nao_avaliadas(self, queryset):
        return queryset.exclude(
            analisedocumental__analise_documental__tipo_analise__nome=self.tipo_analise
        ).distinct()
    @tab(name="Minhas avaliações")
    def minhas_avaliacoes(self, queryset):
        return queryset.filter(
            analisedocumental__analise_documental__tipo_analise__nome=self.tipo_analise,
            analisedocumental__analise_documental__servidor_setor=f"{self.profile.user.get_full_name()} ({self.profile.user})",
        ).distinct()
    @tab(name="Todas avaliadas")
    def avaliadas(self, queryset):
        return queryset.filter(
            analisedocumental__analise_documental__tipo_analise__nome=self.tipo_analise
        ).distinct()
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = self.titulo
        bc = BreadCrumb()
        data["breadcrumb"] = bc
        if self.profile.is_administrador or self.profile.is_coordenador:
            bc.add_many(
                [
                    ("Admin", reverse("admin:index")),
                    (
                        "Processos Seletivos",
                        reverse("admin:app_list", args=["processoseletivo"]),
                    ),
                    (
                        "Análises de Documentos",
                        reverse("admin:processoseletivo_analisedocumental_changelist"),
                    ),
                ]
            )
        bc.add(self.titulo, "")
        return data
    def get_tabs(self):
        tabs = list(super().get_tabs())
        if self.profile.is_administrador or self.profile.is_coordenador:
            tabs.remove("minhas_avaliacoes")
        elif self.profile.is_medico or self.profile.is_caest:
            tabs.remove("avaliadas")
        else:
            tabs = []
        return tabs
class AvaliacaoDocumentalCreateView(
    RevisionMixin, GroupRequiredMixin, generic.CreateView
):
    form_class = forms.AvaliacaoDocumentalForm
    group_required = []
    model = models.AvaliacaoDocumental
    raise_exception = True
    success_url = ""
    tipo_analise = None
    titulo = "Nova avaliação de documentos"
    changelist_name = None
    changelist_url = None
    def dispatch(self, request, *args, **kwargs):
        self.inscricao = get_object_or_404(
            models.Inscricao, pk=self.kwargs.get("inscricao_pk")
        )
        self.confirmacao_interesse = get_object_or_404(
            models.ConfirmacaoInteresse, inscricao=self.inscricao
        )
        return super().dispatch(request, *args, **kwargs)
    def get_changelist_name(self):
        if not self.changelist_name:
            raise ImproperlyConfigured(
                "{0} is missing the changelist_name attribute. Define {0}.changelist_name, or override "
                "{0}.get_changelist_name().".format(self.__class__.__name__)
            )
        return self.changelist_name
    def get_changelist_url(self):
        if not self.changelist_url:
            raise ImproperlyConfigured(
                "{0} is missing the changelist_url attribute. Define {0}.changelist_url, or override "
                "{0}.get_changelist_url().".format(self.__class__.__name__)
            )
        return self.changelist_url
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = self.titulo
        bc = BreadCrumb()
        data["breadcrumb"] = bc
        if (
            self.request.user.is_superuser
            or models.is_sistemico(self.request.user)
            or models.is_admin_campus(self.request.user)
        ):
            bc.add_many(
                [
                    ("Admin", reverse("admin:index")),
                    (
                        "Processos Seletivos",
                        reverse("admin:app_list", args=["processoseletivo"]),
                    ),
                    (
                        "Análises de Documentos",
                        reverse("admin:processoseletivo_analisedocumental_changelist"),
                    ),
                ]
            )
        bc.add(self.get_changelist_name(), reverse(self.get_changelist_url()))
        bc.add(self.titulo, "")
        data["nome_botao"] = "Salvar"
        data["inscricao"] = self.inscricao
        return data
    def get_initial(self):
        initial = super().get_initial()
        analise_documental, create = models.AnaliseDocumental.objects.get_or_create(
            confirmacao_interesse=self.confirmacao_interesse,
            defaults={
                "data": date.today(),
                "situacao_final": False,
                "observacao": "Falta preencher o restante da análise de documentação.",
            },
        )
        initial["analise_documental"] = analise_documental
        initial["data"] = date.today()
        initial[
            "servidor_setor"
        ] = f"{self.request.user.get_full_name()} ({self.request.user})"
        initial["tipo_analise"] = models.TipoAnalise.objects.get(nome=self.tipo_analise)
        return initial
    def form_valid(self, form):
        messages.success(
            self.request,
            f"Avaliação de {self.inscricao.candidato.pessoa} foi criada com sucesso.",
        )
        return super().form_valid(form)
class AvaliacaoDocumentalUpdateView(
    RevisionMixin, GroupRequiredMixin, generic.UpdateView
):
    form_class = forms.AvaliacaoDocumentalUpdateForm
    group_required = []
    model = models.AvaliacaoDocumental
    raise_exception = True
    success_url = ""
    tipo_analise = None
    titulo = "Editar avaliação de documentos"
    changelist_name = None
    changelist_url = None
    def get_changelist_name(self):
        if not self.changelist_name:
            raise ImproperlyConfigured(
                "{0} is missing the changelist_name attribute. Define {0}.changelist_name, or override "
                "{0}.get_changelist_name().".format(self.__class__.__name__)
            )
        return self.changelist_name
    def get_changelist_url(self):
        if not self.changelist_url:
            raise ImproperlyConfigured(
                "{0} is missing the changelist_url attribute. Define {0}.changelist_url, or override "
                "{0}.get_changelist_url().".format(self.__class__.__name__)
            )
        return self.changelist_url
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = self.titulo
        bc = BreadCrumb()
        data["breadcrumb"] = bc
        if (
            self.request.user.is_superuser
            or models.is_sistemico(self.request.user)
            or models.is_admin_campus(self.request.user)
        ):
            bc.add_many(
                [
                    ("Admin", reverse("admin:index")),
                    (
                        "Processos Seletivos",
                        reverse("admin:app_list", args=["processoseletivo"]),
                    ),
                    (
                        "Análises de Documentos",
                        reverse("admin:processoseletivo_analisedocumental_changelist"),
                    ),
                ]
            )
        bc.add(self.get_changelist_name(), reverse(self.get_changelist_url()))
        bc.add(self.titulo, "")
        data["nome_botao"] = "Salvar"
        return data
    def form_valid(self, form):
        avaliacao = form.save()
        avaliacao.servidor_setor = (
            f"{self.request.user.get_full_name()} ({self.request.user})"
        )
        avaliacao.save()
        candidato = (
            self.object.analise_documental.confirmacao_interesse.inscricao.candidato.pessoa
        )
        messages.success(
            self.request, f"Avaliação de {candidato} foi atualizada com sucesso."
        )
        return super().form_valid(form)
class AvaliacaoDocumentalDeleteView(
    RevisionMixin, GroupRequiredMixin, generic.DeleteView
):
    changelist_name = None
    changelist_url = None
    group_required = []
    model = models.AvaliacaoDocumental
    raise_exception = True
    success_url = ""
    titulo = "Excluir avaliação de documentos"
    def get_changelist_name(self):
        if not self.changelist_name:
            raise ImproperlyConfigured(
                "{0} is missing the changelist_name attribute. Define {0}.changelist_name, or override "
                "{0}.get_changelist_name().".format(self.__class__.__name__)
            )
        return self.changelist_name
    def get_changelist_url(self):
        if not self.changelist_url:
            raise ImproperlyConfigured(
                "{0} is missing the changelist_url attribute. Define {0}.changelist_url, or override "
                "{0}.get_changelist_url().".format(self.__class__.__name__)
            )
        return self.changelist_url
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = self.titulo
        bc = BreadCrumb()
        data["breadcrumb"] = bc
        if (
            self.request.user.is_superuser
            or models.is_sistemico(self.request.user)
            or models.is_admin_campus(self.request.user)
        ):
            bc.add_many(
                [
                    ("Admin", reverse("admin:index")),
                    (
                        "Processos Seletivos",
                        reverse("admin:app_list", args=["processoseletivo"]),
                    ),
                    (
                        "Análises de Documentos",
                        reverse("admin:processoseletivo_analisedocumental_changelist"),
                    ),
                ]
            )
        bc.add(self.get_changelist_name(), reverse(self.get_changelist_url()))
        bc.add(self.titulo, "")
        data["nome_botao"] = "Confirmar"
        return data
    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().pode_excluir():
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)
class AvaliacaoDocumentalDetailView(GroupRequiredMixin, generic.DetailView):
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI]
    model = models.AvaliacaoDocumental
    raise_exception = True
    changelist_name = None
    changelist_url = None
    def get_titulo(self):
        return f"Avaliação documental de {self.get_object().analise_documental.confirmacao_interesse.inscricao.candidato}"
    def get_changelist_name(self):
        if not self.changelist_name:
            raise ImproperlyConfigured(
                "{0} is missing the changelist_name attribute. Define {0}.changelist_name, or override "
                "{0}.get_changelist_name().".format(self.__class__.__name__)
            )
        return self.changelist_name
    def get_changelist_url(self):
        if not self.changelist_url:
            raise ImproperlyConfigured(
                "{0} is missing the changelist_url attribute. Define {0}.changelist_url, or override "
                "{0}.get_changelist_url().".format(self.__class__.__name__)
            )
        return self.changelist_url
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = self.get_titulo()
        bc = BreadCrumb()
        data["breadcrumb"] = bc
        if (
            self.request.user.is_superuser
            or models.is_sistemico(self.request.user)
            or models.is_admin_campus(self.request.user)
        ):
            bc.add_many(
                [
                    ("Admin", reverse("admin:index")),
                    (
                        "Processos Seletivos",
                        reverse("admin:app_list", args=["processoseletivo"]),
                    ),
                    (
                        "Análises de Documentos",
                        reverse("admin:processoseletivo_analisedocumental_changelist"),
                    ),
                ]
            )
        bc.add(self.get_changelist_name(), reverse(self.get_changelist_url()))
        bc.add(self.get_titulo(), "")
        return data
    def has_permission(self):
        perms = super().has_permission()
        if perms and not (
            self.request.user.is_superuser or models.is_sistemico(self.request.user)
        ):
            campus = (
                self.get_object().analise_documental.confirmacao_interesse.inscricao.curso.campus
            )
            return campus in self.request.user.lotacoes.all()
        return perms
class ImprimirAvaliacaoDocumentalView(
    GroupRequiredMixin, SingleObjectMixin, generic.View
):
    group_required = [
        models.GRUPO_SISTEMICO,
        models.GRUPO_CAMPI,
        models.GRUPO_MEDICOS,
        models.GRUPO_CAEST,
    ]
    model = models.AvaliacaoDocumental
    raise_exception = True
    def get(self, *args, **kwargs):
        pdf_report = PdfReport(
            pdf.FormularioAnaliseDocumental(self.get_object()).story(), pages_count=0
        ).generate()
        return PDFResponse(pdf_report, nome="avaliacao-pre-matricula.pdf")
class AvaliacaoMedicaListView(AvaliacaoDocumentalListView):
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI, models.GRUPO_MEDICOS]
    tipo_analise = models.TipoAnalise.TIPO_AVALIACAO_MEDICA
    add_url = "avaliacao_medica_add"
    change_url = "avaliacao_medica_update"
    delete_url = "avaliacao_medica_delete"
    detail_url = "avaliacao_medica_detail"
    titulo = "Avaliações de Documentação Médica"
    def get_queryset(self):
        params = {
            "etapa__in": [
                e
                for e in models.Etapa.objects.all()
                if e.analise_documentacao_gerenciada
            ],
            "inscricao__modalidade__in": models.Modalidade.ids_cota_pcd(),
        }
        if not self.profile.is_administrador and (
            self.profile.is_coordenador or self.profile.is_medico
        ):
            params.update(
                {"inscricao__curso__campus__in": self.profile.user.lotacoes.all()}
            )
        return super().get_queryset().filter(**params)
class AvaliacaoMedicaCreateView(AvaliacaoDocumentalCreateView):
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI, models.GRUPO_MEDICOS]
    success_url = reverse_lazy("avaliacao_medica_changelist")
    tipo_analise = models.TipoAnalise.TIPO_AVALIACAO_MEDICA
    titulo = "Nova avaliação médica"
    changelist_name = "Documentações Médicas"
    changelist_url = "avaliacao_medica_changelist"
class AvaliacaoMedicaUpdateView(AvaliacaoDocumentalUpdateView):
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI, models.GRUPO_MEDICOS]
    success_url = reverse_lazy("avaliacao_medica_changelist")
    tipo_analise = models.TipoAnalise.TIPO_AVALIACAO_MEDICA
    titulo = "Editar avaliação médica"
    changelist_name = "Documentações Médicas"
    changelist_url = "avaliacao_medica_changelist"
class AvaliacaoMedicaDeleteView(AvaliacaoDocumentalDeleteView):
    changelist_name = "Documentações Médicas"
    changelist_url = "avaliacao_medica_changelist"
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI, models.GRUPO_MEDICOS]
    success_url = reverse_lazy("avaliacao_medica_changelist")
    titulo = "Excluir avaliação médica"
class AvaliacaoMedicaDetailView(AvaliacaoDocumentalDetailView):
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI, models.GRUPO_MEDICOS]
    changelist_name = "Documentações Médicas"
    changelist_url = "avaliacao_medica_changelist"
    def get_titulo(self):
        return f"Avaliação médica de {self.get_object().analise_documental.confirmacao_interesse.inscricao.candidato}"
class AvaliacaoSocioeconomicaListView(AvaliacaoDocumentalListView):
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI, models.GRUPO_CAEST]
    tipo_analise = models.TipoAnalise.TIPO_AVALIACAO_SOCIOECONOMICA
    add_url = "avaliacao_socioeconomica_add"
    change_url = "avaliacao_socioeconomica_update"
    delete_url = "avaliacao_socioeconomica_delete"
    detail_url = "avaliacao_socioeconomica_detail"
    titulo = "Avaliações de Documentação Socioeconômica"
    def get_queryset(self):
        params = {
            "etapa__in": [
                e
                for e in models.Etapa.objects.all()
                if e.analise_documentacao_gerenciada
            ],
            "inscricao__modalidade__in": models.Modalidade.ids_cota_renda()
            + [models.ModalidadeEnum.rurais],
        }
        if not self.profile.is_administrador and (
            self.profile.is_coordenador or self.profile.is_caest
        ):
            params.update(
                {"inscricao__curso__campus__in": self.profile.user.lotacoes.all()}
            )
        return super().get_queryset().filter(**params)
class AvaliacaoSocioeconomicaCreateView(AvaliacaoDocumentalCreateView):
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI, models.GRUPO_CAEST]
    success_url = reverse_lazy("avaliacao_socioeconomica_changelist")
    tipo_analise = models.TipoAnalise.TIPO_AVALIACAO_SOCIOECONOMICA
    titulo = "Nova avaliação socioeconômica"
    changelist_name = "Documentações Socioeconômicas"
    changelist_url = "avaliacao_socioeconomica_changelist"
class AvaliacaoSocioeconomicaUpdateView(AvaliacaoDocumentalUpdateView):
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI, models.GRUPO_CAEST]
    success_url = reverse_lazy("avaliacao_socioeconomica_changelist")
    tipo_analise = models.TipoAnalise.TIPO_AVALIACAO_SOCIOECONOMICA
    titulo = "Editar avaliação socioeconômica"
    changelist_name = "Documentações Socioeconômicas"
    changelist_url = "avaliacao_socioeconomica_changelist"
class AvaliacaoSocioEconomicaDeleteView(AvaliacaoDocumentalDeleteView):
    changelist_name = "Documentações Socioeconômicas"
    changelist_url = "avaliacao_socioeconomica_changelist"
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI, models.GRUPO_CAEST]
    success_url = reverse_lazy("avaliacao_socioeconomica_changelist")
    titulo = "Excluir avaliação socioeconômica"
class AvaliacaoSocioeconomicaDetailView(AvaliacaoDocumentalDetailView):
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI, models.GRUPO_CAEST]
    changelist_name = "Documentações Socioeconômicas"
    changelist_url = "avaliacao_socioeconomica_changelist"
    def get_titulo(self):
        return f"Avaliação socioeconômica de {self.get_object().analise_documental.confirmacao_interesse.inscricao.candidato}"
class ServidorLotacaoListView(GroupRequiredMixin, ListView):
    template_name = "reuse/listview.html"
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI]
    raise_exception = True
    list_display = ("matricula", "nome", "campus", "acoes")
    model = User
    ordering = ["first_name", "last_name", "username"]
    profile_checker = [
        ("coordenador", models.GRUPO_CAMPI),
        ("administrador", models.GRUPO_SISTEMICO),
    ]
    @column("Campus")
    def campus(self, obj):
        resultado = "-"
        campi = obj.lotacoes.all()
        if campi.exists():
            campi_li = ""
            for campus in campi:
                campi_li += f"<li>{campus}</li>"
            resultado = f"<ul>{campi_li}</ul>"
        return mark_safe(resultado)
    @column("Nome")
    def nome(self, obj):
        return obj.get_full_name()
    @column("Matrícula")
    def matricula(self, obj):
        return obj.username
    @menu("Opções", col="Ações")
    def acoes(self, menu_obj: ListView.menu_class, obj: User) -> None:
        pass
    def get_breadcrumb(self):
        return ((self.get_title(), ""),)
class ServidorLotacaoUpdateView(GroupRequiredMixin, generic.FormView):
    form_class = forms.ServidorLotacaoForm
    group_required = [models.GRUPO_SISTEMICO, models.GRUPO_CAMPI]
    groups = None
    object_name = ""
    raise_exception = True
    success_url = ""
    template_name = "reuse/display_form.html"
    def get_object(self):
        pk = self.kwargs.get("pk", None)
        if pk:
            return User.objects.get(pk=pk)
        return None
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.get_object():
            titulo = f"Editar {self.get_object_name().lower()}"
        else:
            titulo = f"Adicionar novo {self.get_object_name().lower()}"
        data["titulo"] = titulo
        data["nome_botao"] = "Salvar"
        data["breadcrumb"] = BreadCrumb.create(
            (self.get_object_name(), self.success_url), (titulo, "")
        )
        return data
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs
    def get_initial(self):
        initial = super().get_initial()
        if not initial:
            initial = {}
        servidor = self.get_object()
        if servidor:
            initial["servidor"] = servidor
            initial["campi"] = [c.id for c in servidor.lotacoes.all()]
        return initial
    def form_valid(self, form):
        form.save()
        servidor = form.cleaned_data.get("servidor")
        self.set_permission(servidor)
        if self.get_object():
            msg = f"{self.get_object_name()} atualizado com sucesso."
        else:
            msg = f"{self.get_object_name()} criado com sucesso."
        messages.success(self.request, msg)
        return super().form_valid(form)
    def set_permission(self, servidor):
        groups = Group.objects.filter(name__in=self.get_groups())
        servidor.groups.add(*groups)
    def get_groups(self):
        """
        Override this method to override the groups attribute.
        Must return an iterable.
        """
        if self.groups is None:
            raise ImproperlyConfigured(
                "{0} is missing the groups attribute. Define {0}.groups, or override "
                "{0}.get_groups().".format(self.__class__.__name__)
            )
        if isinstance(self.groups, str):
            groups = (self.groups,)
        else:
            groups = self.groups
        return groups
    def get_object_name(self):
        return self.object_name or "Usuário"
class MedicoListView(ServidorLotacaoListView):
    @menu("Opções", col="Ações")
    def acoes(self, menu_obj: ListView.menu_class, obj: User) -> None:
        menu_obj.add("Editar campi", reverse("medico_change", kwargs=dict(pk=obj.id)))
    def get_title(self):
        return "Médicos"
    def get_button_area(self):
        menu_class = self.get_menu_class()
        menu_adicionar = menu_class("Adicionar", button_css="success")
        menu_adicionar.add("Novo Médico", reverse("medico_add"))
        return [menu_adicionar]
    def get_queryset(self):
        medicos_group = Group.objects.get(name=models.GRUPO_MEDICOS)
        params = {"groups": medicos_group}
        if not self.profile.is_administrador and self.profile.is_coordenador:
            params.update({"lotacoes__in": self.profile.user.lotacoes.all()})
        return super().get_queryset().filter(**params)
class MedicoUpdateView(ServidorLotacaoUpdateView):
    groups = models.GRUPO_MEDICOS
    object_name = "Médico"
    success_url = reverse_lazy("medico_changelist")
class CaestListView(ServidorLotacaoListView):
    @menu("Opções", col="Ações")
    def acoes(self, menu_obj: ListView.menu_class, obj: User) -> None:
        menu_obj.add("Editar campi", reverse("caest_change", kwargs=dict(pk=obj.id)))
    def get_title(self):
        return "Servidores CAEST"
    def get_button_area(self):
        menu_class = self.get_menu_class()
        menu_adicionar = menu_class("Adicionar", button_css="success")
        menu_adicionar.add("Novo Servidor", reverse("caest_add"))
        return [menu_adicionar]
    def get_queryset(self):
        caest_group = Group.objects.get(name=models.GRUPO_CAEST)
        params = {"groups": caest_group}
        if not self.profile.is_administrador and self.profile.is_coordenador:
            params.update({"lotacoes__in": self.profile.user.lotacoes.all()})
        return super().get_queryset().filter(**params)
class CaestUpdateView(ServidorLotacaoUpdateView):
    groups = models.GRUPO_CAEST
    object_name = "Servidor CAEST"
    success_url = reverse_lazy("caest_changelist")
class AutoCompleteCandidato(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_staff:
            return PermissionDenied
        qs = models.Candidato.objects.all()
        if self.q:
            qs = qs.filter(
                Q(pessoa__nome__istartswith=self.q) | Q(pessoa__cpf__istartswith=self.q)
            )
        return qs
    def get_result_label(self, result):
        return f"{result.pessoa.nome} (CPF: {result.pessoa.cpf})"
class AutoCompleteInscricao(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_staff:
            return PermissionDenied
        qs = models.Inscricao.objects.all()
        if self.q:
            qs = qs.filter(
                candidato__pessoa__nome__istartswith=self.q,
                chamada__etapa__encerrada=False,
            ).distinct()
        return qs
class AutoCompleteConfirmacaoInteresse(
    LoginRequiredMixin, autocomplete.Select2QuerySetView
):
    def get_queryset(self):
        if not self.request.user.is_staff:
            return PermissionDenied
        qs = models.ConfirmacaoInteresse.objects.all()
        if self.q:
            qs = qs.filter(
                inscricao__candidato__pessoa__nome__istartswith=self.q,
                etapa__encerrada=False,
            ).distinct()
        return qs
class AutoCompleteAnaliseDocumental(
    LoginRequiredMixin, autocomplete.Select2QuerySetView
):
    def get_queryset(self):
        if not self.request.user.is_staff:
            return PermissionDenied
        qs = models.AnaliseDocumental.objects.all()
        if self.q:
            qs = qs.filter(
                confirmacao_interesse__inscricao__candidato__pessoa__nome__istartswith=self.q,
                situacao_final=False,
                confirmacao_interesse__etapa__encerrada=False,
            ).distinct()
        return qs
#VIEWS ADICIONADAS POSTERIORMENTE PARA COLOCAR CONTEÚDO DO PORTAL NO SISTEMA DE INSCRIC'~AO#
class ProcessoDuvidas(generic.TemplateView):
    template_name = "processoseletivo/portal/duvidas.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['onde_estou'] =  "Dúvidas"
        return context

class ProcessoListaCursos(generic.TemplateView):
    template_name = "processoseletivo/portal/lista_de_cursos.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['onde_estou'] =  "Lista de Cursos"
        return context

class ProcessoListaCursosIntegrado(generic.TemplateView):
    template_name = "processoseletivo/portal/concorrencia_integrado.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['onde_estou'] =  "Cursos Integrados"
        return context

class ProcessoListaCursosSubsequente(generic.TemplateView):
    template_name = "processoseletivo/portal/concorrencia_subsequente.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['onde_estou'] =  "Cursos Subsequentes"
        return context

class ProcessoListaCursosConcomitante(generic.TemplateView):
    template_name = "processoseletivo/portal/concorrencia_concomitante.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['onde_estou'] =  "Cursos Concomitantes"
        return context

class ProcessoCronograma(generic.TemplateView):
    template_name = "processoseletivo/portal/cronograma.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['onde_estou'] =  "Cronograma"
        return context

class ProcessoDocumentos(generic.TemplateView):
    template_name = "processoseletivo/portal/documento_inscricao.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['onde_estou'] =  "Documentos"
        return context

def ProcessoPcd(request):
    localizacao = {}
    localizacao['onde_estou'] = "PCD"             
    return render(request,'processoseletivo/portal/pcd.html', localizacao)

class ProcessoSistemRvCotas(generic.TemplateView):
    template_name = "processoseletivo/portal/sistema_rv.html"
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['onde_estou'] =  "Cotas"
        return context