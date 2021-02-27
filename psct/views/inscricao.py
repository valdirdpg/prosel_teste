import datetime
import json
import os
import uuid

import reversion
from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.safestring import mark_safe
from django.views import generic
from extra_views import InlineFormSet, UpdateWithInlinesView
from reversion.views import RevisionMixin

from base.custom.datatypes import BreadCrumb
from base.custom.views import ListView
from base.custom.views.decorators import column
from base.custom.views.mixin import AnyGroupRequiredMixin, GroupRequiredMixin
from base.pdf import PDFResponse
from base.shortcuts import get_object_or_permission_denied
from editais import models as models_editais
from processoseletivo.models import ModalidadeEnum
from psct import pdf
from psct.forms import inscricao as forms
from psct.forms.inscricao import EnsinoRegularForm, InscricaoForm
from psct.models import inscricao as models, RespostaCriterio
from psct.tasks.inscricao import generate_pdf
from psct.views.recurso import ListGrupoPermissaoView
from .. import loaders

MENSAGEM_RESUMO = """Atenção: o resumo não é um comprovante de inscrição. Seu comprovante estará disponível na área do
candidato após o encerramento do período de inscrição."""

MENSAGEM_RESUMO_CONFERIR = """Atenção: confira seus dados abaixo. Caso você encontre algum erro, poderá corrigir na
Área do Candidato disponível no menu. Você pode alterar os seus dados durante todo o período de
inscrição do edital."""


class InscricaoEditalView(generic.RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        edital = get_object_or_404(
            models_editais.Edital, pk=int(self.kwargs["edital_pk"])
        )
        url = reverse("responder_questionario_psct", args=[edital.id])
        if not self.request.user.is_authenticated:
            url = f"{reverse('pre_cadastro_candidato_psct')}?next={url}"
        return url


class PermissionCheck(RevisionMixin, UserPassesTestMixin):
    raise_exception = True

    def get_inscricao(self):
        raise NotImplementedError("Você deve implementar o método 'get_inscricao'")

    def test_func(self):
        user = self.request.user
        inscricao = self.get_inscricao()
        if (
            user.is_authenticated
            and inscricao.is_owner(user)
            and inscricao.pode_alterar
        ):
            return True
        else:
            return False


class ViewInscricao(UserPassesTestMixin, generic.DetailView):
    model = models.Inscricao
    raise_exception = True

    def test_func(self):
        user = self.request.user
        inscricao = self.get_object()
        if user.is_authenticated and (
            (inscricao.is_owner(user) and inscricao.pode_visualizar_inscricao())
            or user.has_perm("psct.view_inscricao")
        ):
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        processo = self.object.edital.processo_inscricao
        if processo.pode_emitir_comprovante:
            kwargs["pode_emitir_comprovante"] = processo.pode_emitir_comprovante
        else:
            messages.warning(self.request, MENSAGEM_RESUMO)
        return super().get_context_data(**kwargs)


@login_required(login_url="/login/")
def selecionar_ensino(request, pk):
    pontuacao = get_object_or_404(models.PontuacaoInscricao, pk=pk)
    is_edit = (pontuacao.data_criacao.strftime("%m/%d/%Y %H:%M:%S") != pontuacao.data_atualizacao.strftime("%m/%d/%Y %H:%M:%S"))

    if not (pontuacao.inscricao.pode_alterar):
        raise PermissionDenied()

    if request.method == "GET":
        form = EnsinoRegularForm(pontuacao, is_edit)
        if pontuacao.inscricao.aceite:
            form.fields["aceite"] = forms.forms.BooleanField(label=models.LABEL_ACEITE)
    elif request.method == "POST":
        form = EnsinoRegularForm(pontuacao, is_edit, request.POST)
        if pontuacao.inscricao.aceite:
            form.fields["aceite"] = forms.forms.BooleanField(label=models.LABEL_ACEITE)
        if form.is_valid():
            if form.cleaned_data["ensino"] == "ENSINO_REGULAR":
                pontuacao.ensino_regular = True
            else:
                pontuacao.ensino_regular = False

            with reversion.create_revision():

                if form.cleaned_data["force"]:
                    pontuacao.apagar_notas()

                pontuacao.save()
                pontuacao.criar_notas()

                reversion.set_user(request.user)
                reversion.set_comment("Usuário modificou forma de ensino.")

            return redirect(reverse("notas_inscricao_psct", args=[pk]))
        else:
            if "aceite" in form.data:
                new_data = form.data.copy()
                new_data["aceite"] = False
                form.data = new_data
    else:
        form = None

    back_url = reverse("update_inscricao_psct", kwargs=dict(pk=pontuacao.inscricao_id))
    return render(
        request,
        "psct/selecionar_ensino.html",
        dict(form=form, pontuacao=pontuacao, back_url=back_url),
    )
    back_url2 = reverse("responder_questionario_psct", kwargs=dict(pk=edital.id))
    return render(
        request,
        "psct/questionario_socioeconomico.html",
        dict(form=form, edital=edital, back_url=back_url2),
    )


class InscricaoViewMixIn:
    def get_cursos(self):
        result = {}
        object = getattr(self, "object", None)
        if object:
            cursos = self.object.edital.processo_inscricao.cursos.order_by(
                "curso__nome"
            )
        else:
            cursos = self.edital.processo_inscricao.cursos.order_by("curso__nome")
        for c in cursos:
            if c.campus_id not in result:
                result[c.campus_id] = []
            result[c.campus_id].append(dict(id=c.id, name=models.format_curso(c)))
        return json.dumps(result)

    def get_success_url(self):
        if self.processo_inscricao.is_curso_tecnico:
            return reverse(
                "selecionar_ensino_psct", kwargs=dict(pk=self.object.pontuacao.pk)
            )
        return reverse("visualizar_inscricao_psct", kwargs=dict(pk=self.object.pk))


class CreateInscricao(
    RevisionMixin, InscricaoViewMixIn, LoginRequiredMixin, generic.CreateView
):
    model = models.Inscricao
    template_name = "psct/create_inscricao.html"
    form_class = InscricaoForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.edital.processo_inscricao.is_curso_tecnico:
            context["titulo"] = "Nova Inscrição - TIPO DE VAGA E ESCOLHA DE CURSO"
        else:
            context["titulo"] = "Nova Inscrição"
        context["is_edit"] = "false"
        context["modalidade_compativel"] = "null"
        form = "form" in kwargs
        if form:
            cotista = kwargs["form"].cleaned_data.get("cotista")
        else:
            cotista = False
        if form and cotista and cotista == "SIM":
            context["hide_modalidades"] = "false"
        else:
            context["hide_modalidades"] = "true"
        context["cursos_json"] = self.get_cursos()
        if not self.request.POST:
            context["campus_id"] = 0
        else:
            context["campus_id"] = self.request.POST.get("campus", 0)
        context["back_url"] = "psct/questionario_socioeconomico/{}/?active=OK".format(self.edital.id)
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"]["candidato"] = self.candidato
        kwargs["initial"]["edital"] = self.edital
        return kwargs

    def get_template_names(self):
        if self.edital.processo_inscricao.is_curso_tecnico:
            if self.edital.processo_inscricao.possui_segunda_opcao:
                return ["psct/inscricao/create_inscricao_tecnico_segunda_opcao.html"]
            return super().get_template_names()
        if self.edital.processo_inscricao.possui_segunda_opcao:
            return ["psct/inscricao/create_inscricao_graduacao_segunda_opcao.html"]
        return ["psct/inscricao/create_inscricao_graduacao.html"]

    def get_form_class(self):
        if self.edital.processo_inscricao.is_curso_tecnico:
            if self.edital.processo_inscricao.possui_segunda_opcao:
                return forms.InscricaoSegundaOpcaoTecnicoForm
            return super().get_form_class()
        if self.edital.processo_inscricao.possui_segunda_opcao:
            return forms.InscricaoSegundaOpcaoGraduacaoForm
        return forms.InscricaoGraduacaoForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        hoje = datetime.date.today()
        if self.request.user.is_authenticated:
            self.candidato = get_object_or_permission_denied(
                models.Candidato, user=self.request.user
            )

        self.edital = get_object_or_permission_denied(
            models.Edital,
            pk=self.kwargs["edital_pk"],
            processo_inscricao__isnull=False,
            processo_inscricao__data_inicio__lte=hoje,
            processo_inscricao__data_encerramento__gte=hoje,
        )
        self.processo_inscricao = self.edital.processo_inscricao

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            inscricao = models.Inscricao.objects.filter(
                candidato=self.candidato, edital=self.edital
            ).first()
            if inscricao:
                return redirect(
                    reverse("update_inscricao_psct", kwargs=dict(pk=inscricao.pk))
                )
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class UpdateInscricao(InscricaoViewMixIn, PermissionCheck, generic.UpdateView):
    model = models.Inscricao
    template_name = "psct/create_inscricao.html"
    form_class = InscricaoForm
    back_url = "psct/questionario_socioeconomico/{}/?active=OK"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.inscricao.is_selecao_curso_tecnico:
            context["titulo"] = "Modificar Inscrição - TIPO DE VAGA E ESCOLHA DE CURSO"
        else:
            context["titulo"] = "Modificar Inscrição"
        form = "form" in kwargs
        if form:
            cotista = kwargs["form"].cleaned_data.get("cotista")
        else:
            cotista = False
        if form and cotista and cotista == "SIM":
            context["hide_modalidades"] = "false"
        else:
            context["hide_modalidades"] = "true"
            # if self.object.modalidade_cota.id != ModalidadeEnum.ampla_concorrencia or (
            #     kwargs.get("form") and kwargs["form"].cleaned_data.get("cotista") == "SIM"
            # ):
            #     context["hide_modalidades"] = "false"
            # else:
            #     context["hide_modalidades"] = "true"
        context["is_edit"] = "true"
        context["modalidade_compativel"] = self.get_modalidade_compativel(self.object.candidato, self.object.edital)
        context["cursos_json"] = self.get_cursos()
        context["campus_id"] = self.object.curso.campus_id
        context["back_url"] = "psct/questionario_socioeconomico/{}/?active=OK".format(self.inscricao.edital.id)
        return context

    def get_modalidade_compativel(self, candidato, edital):
        resposta_pcd = RespostaCriterio.objects.get(resposta_modelo__candidato=candidato,
                                                    resposta_modelo__modelo__edital=edital,
                                                    criterio_alternativa_selecionada__criterio__id=9)
        resposta_baixa_renda = RespostaCriterio.objects.get(resposta_modelo__candidato=candidato,
                                                            resposta_modelo__modelo__edital=edital,
                                                            criterio_alternativa_selecionada__criterio__id=1)
        resposta_ppi = RespostaCriterio.objects.get(resposta_modelo__candidato=candidato,
                                                    resposta_modelo__modelo__edital=edital,
                                                    criterio_alternativa_selecionada__criterio__id=2)
        resposta_escola_publica_fund = RespostaCriterio.objects.get(
            resposta_modelo__candidato=candidato, resposta_modelo__modelo__edital=edital,
            criterio_alternativa_selecionada__criterio__id=10)
        resposta_escola_publica_med = RespostaCriterio.objects.filter(
            resposta_modelo__candidato=candidato, resposta_modelo__modelo__edital=edital,
            criterio_alternativa_selecionada__criterio__id=11)

        marcou_pcd = resposta_pcd.criterio_alternativa_selecionada.posicao == 2
        marcou_baixa_renda = resposta_baixa_renda.criterio_alternativa_selecionada.posicao == 1
        marcou_ppi = resposta_ppi.criterio_alternativa_selecionada.posicao in [1, 2, 4]
        marcou_escola_publica_fund = resposta_escola_publica_fund.criterio_alternativa_selecionada.posicao == 1
        if resposta_escola_publica_med:
            marcou_escola_publica_med = resposta_escola_publica_med[0].criterio_alternativa_selecionada.posicao == 1
        if resposta_escola_publica_med:
            marcou_escola_publica = marcou_escola_publica_med and marcou_escola_publica_fund
        else:
            marcou_escola_publica = marcou_escola_publica_fund
        modalidade_compativel = 3
        if marcou_escola_publica and marcou_baixa_renda and marcou_ppi and marcou_pcd:
            modalidade_compativel = 2
        elif marcou_escola_publica and marcou_baixa_renda and marcou_ppi:
            modalidade_compativel = 8
        elif marcou_escola_publica and marcou_baixa_renda and marcou_pcd:
            modalidade_compativel = 9
        elif marcou_escola_publica and marcou_baixa_renda:
            modalidade_compativel = 6
        elif marcou_escola_publica and marcou_ppi and marcou_pcd:
            modalidade_compativel = 10
        elif marcou_escola_publica and marcou_ppi:
            modalidade_compativel = 5
        elif marcou_escola_publica and marcou_pcd:
            modalidade_compativel = 11
        elif marcou_escola_publica:
            modalidade_compativel = 7
        elif marcou_pcd:
            modalidade_compativel = 4
        return modalidade_compativel

    def get_template_names(self):
        if self.inscricao.is_selecao_curso_tecnico:
            if self.edital.processo_inscricao.possui_segunda_opcao:
                return ["psct/inscricao/create_inscricao_tecnico_segunda_opcao.html"]
            return super().get_template_names()
        if self.edital.processo_inscricao.possui_segunda_opcao:
            return ["psct/inscricao/create_inscricao_graduacao_segunda_opcao.html"]
        return ["psct/inscricao/create_inscricao_graduacao.html"]

    def get_form_class(self):
        if self.inscricao.is_selecao_curso_tecnico:
            if self.edital.processo_inscricao.possui_segunda_opcao:
                return forms.InscricaoSegundaOpcaoTecnicoForm
            return super().get_form_class()
        if self.edital.processo_inscricao.possui_segunda_opcao:
            return forms.InscricaoSegundaOpcaoGraduacaoForm
        return forms.InscricaoGraduacaoForm

    def get_inscricao(self):
        return self.get_object()

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.inscricao = self.get_inscricao()
        self.edital = self.inscricao.edital
        self.processo_inscricao = self.edital.processo_inscricao

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.get_inscricao().aceite and self.inscricao.is_selecao_curso_tecnico:
            form.fields["aceite"] = forms.forms.BooleanField(label=models.LABEL_ACEITE)
        return form

    def form_invalid(self, form):
        if "aceite" in form.data:
            new_data = form.data.copy()
            new_data["aceite"] = False
            form.data = new_data
        return super().form_invalid(form)

    def get_form_kwargs(self):
        if self.inscricao.is_selecao_graduacao:
            self.object.aceite = False

        kwargs = super().get_form_kwargs()
        data = kwargs.get("data", {})
        modalidade_cota = data.get("modalidade_cota")
        cotista = data.get("cotista")
        if data and not modalidade_cota and cotista == "NAO":
            new_data = kwargs["data"].copy()
            new_data["modalidade_cota"] = "3"
            kwargs["data"] = new_data
        kwargs["initial"]["candidato"] = self.inscricao.candidato
        return kwargs


class ComprovanteInline(InlineFormSet):
    model = models.Comprovante
    form_class = forms.ComprovanteForm
    formset_class = forms.ComprovantesFormSet
    exclude = []
    factory_kwargs = {"extra": 0, "max_num": 8}

    def get_factory_kwargs(self):
        kwargs = super().get_factory_kwargs()
        kwargs["min_num"] = 1
        kwargs["validate_min"] = True
        kwargs["validate_max"] = True
        return kwargs

    def construct_formset(self):
        formset = super().construct_formset()
        del formset.forms[0].fields["DELETE"]
        return formset


class ComprovantesUpdateView(PermissionCheck, UpdateWithInlinesView):
    template_name = "psct/comprovantes.html"
    model = models.Inscricao
    inlines = [ComprovanteInline]
    fields = ["aceite"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Documento de Histórico Escolar"
        context["back_url"] = reverse(
            "notas_inscricao_psct", kwargs=dict(pk=self.object.pontuacao.pk)
        )
        return context

    def get_success_url(self):
        messages.success(self.request, "Inscrição concluída com sucesso!")
        return reverse("visualizar_inscricao_psct", kwargs=dict(pk=self.object.pk))

    def get_inscricao(self):
        return self.get_object()

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["aceite"].required = True
        return form

    def get_initial(self):
        initial = super().get_initial()
        initial["aceite"] = False
        return initial

    def forms_invalid(self, form, inlines):
        if "aceite" in form.data:
            new_data = form.data.copy()
            new_data["aceite"] = False
            form.data = new_data
        return super().forms_invalid(form, inlines)

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except MultiValueDictKeyError:
            messages.error(
                self.request,
                "Infelizmente ocorreu um erro ao processar sua requisição. Por favor, tente novamente.",
            )
            return redirect("comprovantes_inscricao_psct", pk=self.object.pk)


class NotasInline(InlineFormSet):
    model = models.NotaAnual
    fields = ("ano", "portugues", "matematica", "historia", "geografia")

    form_class = forms.NotaAnualForm
    factory_kwargs = {"extra": 0, "can_delete": False}

    def get_factory_kwargs(self):
        kwargs = super().get_factory_kwargs()
        fields = list(kwargs["fields"])
        if not self.object.inscricao.is_integrado:
            fields.remove("historia")
            fields.remove("geografia")
        if not self.object.ensino_regular:
            fields.remove("ano")

        kwargs["fields"] = tuple(fields)
        return kwargs

    def get_form_class(self):
        form = super().get_form_class()
        if not self.object.ensino_regular:
            return forms.SupletivoForm
        return form


class NotasUpdateView(PermissionCheck, UpdateWithInlinesView):
    template_name = "psct/notas.html"
    model = models.PontuacaoInscricao
    inlines = [NotasInline]
    fields = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Notas da Inscrição"
        context["back_url"] = reverse(
            "selecionar_ensino_psct", kwargs=dict(pk=self.object.pk)
        )
        return context

    def get_success_url(self):
        return reverse(
            "comprovantes_inscricao_psct", kwargs=dict(pk=self.object.inscricao_id)
        )

    def get_inscricao(self):
        return self.get_object().inscricao

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.get_inscricao().aceite:
            form.fields["aceite"] = forms.forms.BooleanField(label=models.LABEL_ACEITE)
        return form

    def forms_invalid(self, form, inlines):
        if "aceite" in form.data:
            new_data = form.data.copy()
            new_data["aceite"] = False
            form.data = new_data
        return super().forms_invalid(form, inlines)


class CancelarInscricaoView(PermissionCheck, generic.FormView):
    success_url = "/psct/"
    form_class = forms.forms.Form
    template_name = "psct/inscricao/cancelar.html"

    def form_valid(self, form):
        models.CancelamentoInscricao.objects.create(
            inscricao_id=self.kwargs["pk"], usuario=self.request.user
        )
        messages.success(self.request, "Inscrição cancelada com sucesso!")
        return super().form_valid(form)

    def get_inscricao(self):
        return models.Inscricao.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["inscricao"] = self.get_inscricao()
        return data


class RemoverCancelamentoView(PermissionCheck, generic.FormView):
    success_url = "/psct/"
    form_class = forms.forms.Form
    template_name = "psct/inscricao/remover_cancelamento.html"

    def test_func(self):
        user = self.request.user
        inscricao = self.get_inscricao()
        if (
            user.is_authenticated
            and inscricao.is_owner(user)
            and inscricao.em_periodo_inscricao
            and inscricao.is_cancelada
        ):
            return True
        else:
            return False

    def form_valid(self, form):
        if not self.get_inscricao().pode_desfazer_cancelamento() and not self.get_inscricao().candidato.has_todas_insc_canceladas():
            messages.error(self.request, "Você não pode desfazer este cancelamento, pois existe uma inscrição ativa.")
            return super().form_invalid(form)
        models.CancelamentoInscricao.objects.filter(
            inscricao_id=self.kwargs["pk"]
        ).delete()
        messages.success(self.request, "Cancelamento desfeito com sucesso!")
        return super().form_valid(form)

    def get_inscricao(self):
        return models.Inscricao.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["inscricao"] = self.get_inscricao()
        return data


class AdicionarCursoEditalView(GroupRequiredMixin, generic.FormView):
    template_name = "psct/inscricao/adicionar_vaga_curso.html"
    raise_exception = True
    group_required = "Administradores PSCT"
    form_class = forms.forms.Form

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Cadastro de vagas por curso de edital"
        data["processo_inscricao"] = models.ProcessoInscricao.objects.get(
            pk=self.kwargs["pk"]
        )
        data["breadcrumb"] = BreadCrumb.create(
            (
                "Processos de inscrição dos editais",
                reverse("admin:psct_processoinscricao_changelist"),
            ),
            ("Adicionar vagas", ""),
        )
        return data

    def form_valid(self, form):
        edital = self.processo_inscricao.edital
        for curso in self.processo_inscricao.cursos.all():
            if not models.CursoEdital.objects.filter(
                edital=edital, curso=curso
            ).exists():
                models.CursoEdital.objects.create(edital=edital, curso=curso)

        messages.success(self.request, "Adicionados curso do edital com sucesso!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("admin:psct_cursoedital_changelist")

    def dispatch(self, request, *args, **kwargs):
        self.processo_inscricao = get_object_or_404(
            models.ProcessoInscricao, pk=self.kwargs["pk"]
        )
        return super().dispatch(request, *args, **kwargs)


class ComprovanteInscricaoView(UserPassesTestMixin, generic.View):
    raise_exception = True

    def get_inscricao(self):
        return models.Inscricao.objects.get(id=self.kwargs["pk"])

    def test_func(self):
        user = self.request.user
        inscricao = self.get_inscricao()
        if (
            user.is_authenticated
            and inscricao.is_owner(user)
            and inscricao.pode_visualizar_inscricao()
            and inscricao.edital.processo_inscricao.pode_emitir_comprovante
        ):
            return True
        else:
            return False

    def get(self, request, pk):

        comprovante = models.ComprovanteInscricao.objects.filter(
            inscricao=self.get_inscricao()
        ).last()
        if not comprovante:
            chave = uuid.uuid4().hex
            conteudo = pdf.imprimir_comprovante(request, pk, chave)
            filename = os.path.join("psct", "comprovantes_inscricao", f"{chave}.pdf")
            if default_storage.exists(
                filename
            ):  # garantia de não sobrescrever, na pior das hipóteses
                raise ValueError(
                    f"Arquivo de comprovante de inscrição {filename} já existe."
                )
            arquivo = default_storage.save(filename, ContentFile(conteudo))
            comprovante = models.ComprovanteInscricao.objects.create(
                inscricao=self.get_inscricao(), chave=chave, arquivo=arquivo
            )

        return PDFResponse(comprovante.arquivo, nome="Comprovante.pdf")


class ListaInscritosPdf(PermissionRequiredMixin, generic.View):
    login_url = "/admin/login/"
    raise_exception = True
    permission_required = "psct.add_list_inscritos"

    def get(self, request, pk):
        preliminar = self.request.GET.get("preliminar")
        if preliminar:
            generate_pdf.delay(request.user.id, pk, lista_final=False)
        else:
            generate_pdf.delay(request.user.id, pk, lista_final=True)
        messages.info(
            request,
            "Seu trabalho está sendo processado e em breve você receberá um e-mail com o arquivo.",
        )
        edital = models.Edital.objects.get(id=pk)
        return redirect(
            "admin:psct_processoinscricao_change", edital.processo_inscricao.pk
        )


class ListComprovanteView(AnyGroupRequiredMixin, ListView):
    model = models.ComprovanteInscricao
    show_numbers = True
    list_display = ("chave", "candidato", "link")
    field_filters = ("inscricao__edital",)
    group_required = ("Validador de Comprovantes PSCT", "Administradores PSCT")
    search_fields = ("chave",)
    raise_exception = True
    always_show_form = True
    ordering = ("-id",)

    def get_breadcrumb(self):
        return (("Comprovantes", ""),)

    @column("Candidato")
    def candidato(self, obj):
        return obj.inscricao.candidato

    @mark_safe
    @column("Arquivo")
    def link(self, obj):
        return f'<a href="{obj.arquivo.url}" target="_blank">Visualizar</a>'


class AutoCompleteCandidato(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_staff:
            return PermissionDenied

        qs = models.Candidato.objects.all()

        if self.q:
            qs = qs.filter(nome__istartswith=self.q).distinct()

        return qs


class ListValidadorView(ListGrupoPermissaoView):
    group_name = "Validador de Comprovantes PSCT"
    title_group = "Validadores de Comprovantes"


class ImportarNotasEnemView(GroupRequiredMixin, generic.FormView):
    form_class = forms.ImportarNotasEnemForm
    group_required = "Administradores PSCT"
    raise_exception = True
    success_url = reverse_lazy("base")
    template_name = "psct/inscricao/importar_enem.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Importar notas do Enem"
        data["back_url"] = reverse("base")
        data["nome_botao"] = "Importar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Admin", reverse("admin:index")),
            ("PSCT", reverse("admin:app_list", args=["psct"])),
            ("Importar notas do Enem", "")
        )
        return data

    def form_valid(self, form):
        edital = form.cleaned_data["edital"]
        ano = form.cleaned_data["ano"]
        arquivo = form.cleaned_data["arquivo"]
        loader = loaders.EnemLoader(
            arquivo,
            encoding="UTF-8-sig",
            delimiter=";",
            initial_context=dict(edital=edital, ano=ano),
        )
        loader.run()
        messages.info(self.request, "Notas importadas com sucesso.")
        return super().form_valid(form)
