from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from reversion.views import RevisionMixin

from base import models as base_models
from base import utils as base_utils
from base.custom.datatypes import BreadCrumb
from base.custom.views.mixin import GroupRequiredMixin
from base.pdf import PDFResponse
from candidatos import forms, models, pdf, utils
from processoseletivo import models as models_ps


class UserPreMatriculaMixin(UserPassesTestMixin):
    def test_func(self):
        return utils.is_candidato_prematricula(self.request.user)


class CandidatoBaseUpdateView(generic.UpdateView):
    raise_exception = True
    model = base_models.PessoaFisica
    form_class = forms.DadosBasicosForm
    template_name = "candidatos/generic_prematricula_form.html"

    def get_object(self, queryset=None):
        return self.request.user.pessoa

    def form_invalid(self, form):
        if "declara_veracidade" in form.data:
            new_data = form.data.copy()
            new_data["declara_veracidade"] = False
            form.data = new_data
        return super().form_invalid(form)


class DadosBasicosUpdateView(
    RevisionMixin, GroupRequiredMixin, CandidatoBaseUpdateView
):
    """
    View utilizada na atualização de dados básicos do cadastro geral
    """

    group_required = "Candidatos"

    def get_context_data(self, **kwargs):
        data = super().get_context_data()
        titulo = f"Meus Dados: {self.request.user.pessoa}"
        data["titulo"] = titulo
        data["form_class"] = "form-horizontal"
        data["label_width_col"] = "4"
        data["input_width_col"] = "8"
        data["breadcrumb"] = BreadCrumb.create((titulo, ""))
        return data

    def get_success_url(self):
        messages.success(self.request, "Dados básicos foram atualizados com sucesso.")
        return reverse("dados_basicos_candidato")


class CandidatoUpdateView(
    RevisionMixin, UserPreMatriculaMixin, CandidatoBaseUpdateView
):
    """
    View utilizada na atualização de dados básicos da pré-matrícula
    """

    form_class = forms.CandidatoPreMatriculaForm

    def get_context_data(self, **kwargs):
        data = super().get_context_data()
        titulo = f"Dados Básicos de {self.request.user.pessoa}"
        data["titulo"] = titulo
        data["breadcrumb"] = BreadCrumb.create(("Pré-Matrícula", ""), (titulo, ""))
        return data

    def get_success_url(self):
        messages.success(self.request, "Dados básicos foram atualizados com sucesso.")
        if self.object.caracterizacao_set.exists():
            url = "editar_caracterizacao_prematricula"
        else:
            url = "adicionar_caracterizacao_prematricula"
        return reverse(url, args=[self.object.pk])


class CaracterizacaoBaseView(UserPreMatriculaMixin):
    form_class = forms.CaracterizacaoForm
    model = models.Caracterizacao
    raise_exception = True
    template_name = "candidatos/generic_prematricula_form.html"

    def get(self, request, *args, **kwargs):
        if not self.candidato.has_dados_suap_completos():
            messages.warning(
                request,
                "Antes de preencher a caracterização socioeconômica, você precisa atualizar "
                "os seus dados básicos.",
            )
            return redirect("dados_basicos_prematricula")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data()
        titulo = f"Dados Socioeconômicos de {self.request.user.pessoa}"
        data["titulo"] = titulo
        data["form_class"] = "form-horizontal"
        data["label_width_col"] = "6"
        data["input_width_col"] = "6"
        data["breadcrumb"] = BreadCrumb.create(("Pré-Matrícula", ""), (titulo, ""))
        return data

    def get_initial(self):
        initial = super().get_initial()

        # Obriga o candidato a sempre clicar no CheckBox quando atualizar os dados
        initial["declara_veracidade"] = False

        initial["nome_pai"] = self.candidato.nome_pai
        initial["nome_mae"] = self.candidato.nome_mae
        initial["candidato"] = self.candidato
        return initial

    def get_success_url(self):
        messages.success(
            self.request, "Seus dados socioeconômicos foram salvos com sucesso."
        )
        return reverse("chamadas_prematricula")

    def setup(self, request, *args, **kwargs):
        self.candidato = get_object_or_404(models.Candidato, pk=kwargs["pk_candidato"])
        return super().setup(request, *args, **kwargs)

    def test_func(self):
        usuario_candidato = self.request.user.pessoa == self.candidato
        return usuario_candidato and super().test_func()


class CaracterizacaoCreateView(CaracterizacaoBaseView, generic.CreateView):
    pass


class CaracterizacaoUpdateView(CaracterizacaoBaseView, generic.UpdateView):
    def get_object(self, queryset=None):
        return get_object_or_404(models.Caracterizacao, candidato=self.candidato)


@login_required(login_url="/admin/login")
def imprimir_prematricula(request, candidato_pk, chamada_pk):
    return PDFResponse(
        pdf.imprimir_formulario_matricula(request, candidato_pk, chamada_pk),
        nome="Formulario_de_Pre_Matricula.pdf",
    )


class ChamadasCandidatoView(UserPreMatriculaMixin, generic.TemplateView):
    raise_exception = True
    template_name = "candidatos/imprimir_formulario.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        chamadas = context["chamadas"]

        data_inicio_chamadas = sorted(
            [chamada.etapa.data_inicio for chamada in chamadas]
        )
        inicio_ultima_chamada = data_inicio_chamadas[-1]
        dias_passados = base_utils.dias_entre(inicio_ultima_chamada, date.today())

        try:
            caracterizacao = models.Caracterizacao.objects.get(candidato=self.candidato)
        except models.Caracterizacao.DoesNotExist:
            caracterizacao = None
        has_caracterizacao_atualizada = (
            caracterizacao and caracterizacao.is_atualizado_recentemente(dias_passados)
        )
        if (
            not self.candidato.has_dados_suap_completos()
            or not has_caracterizacao_atualizada
        ):
            messages.warning(
                request,
                "Antes de imprimir o formulário de pré-matrícula, você precisa atualizar os seus "
                "dados básicos e, em seguida, os dados socioeconômicos.",
            )
            return redirect("dados_basicos_prematricula")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chamadas = models_ps.Chamada.objects.filter(
            etapa__encerrada=False, inscricoes__candidato=self.candidato.candidato_ps
        )
        context["chamadas"] = chamadas
        context["candidato"] = self.candidato
        return context

    def setup(self, request, *args, **kwargs):
        if hasattr(request.user, "pessoa"):
            self.candidato = request.user.pessoa
        else:
            self.candidato = None
        return super().setup(request, *args, **kwargs)


class ConvocacoesCandidatoView(LoginRequiredMixin, generic.TemplateView):
    raise_exception = True
    template_name = "candidatos/convocacoes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        inscricoes = models_ps.Inscricao.objects.filter(
            chamada__etapa__publica=True, candidato__pessoa__user=user
        )
        context["candidato"] = user.pessoa
        context["inscricoes"] = inscricoes
        return context


class RecursosCandidatoView(LoginRequiredMixin, generic.TemplateView):
    template_name = "candidatos/recursos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = context["pk"]
        user = self.request.user
        candidato_ps = get_object_or_404(models_ps.Candidato, pk=pk)
        if not user.is_staff and candidato_ps != user.candidato:
            raise Http404

        recursos = models_ps.Recurso.objects.filter(
            analise_documental__confirmacao_interesse__inscricao__candidato__id=candidato_ps.id,
            analise_documental__confirmacao_interesse__etapa__encerrada=False,
        )

        context["recursos"] = recursos

        return context
