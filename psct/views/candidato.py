from datetime import datetime

from django.contrib import auth, messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.debug import sensitive_post_parameters
from ifpb_django_permissions.perms import in_any_groups
from reversion.views import RevisionMixin

from base.custom.datatypes import BreadCrumb
from base.custom.views.mixin import GroupRequiredMixin
from base.shortcuts import get_object_or_permission_denied
from candidatos.permissions import Candidatos
from processoseletivo import models as models_ps
from .. import permissions
from ..forms import candidato as forms
from ..models import candidato as models
from ..models import inscricao as models_inscricao


class PSCTView(UserPassesTestMixin, generic.TemplateView):
    template_name = "psct/inscricoes.html"

    def test_func(self):
        user = self.request.user
        if user.is_authenticated and in_any_groups(
            user, [Candidatos, permissions.CandidatosPSCT]
        ):
            return True
        elif user.is_authenticated:
            self.raise_exception = True
            messages.warning(
                self.request,
                "Atenção! Você está logado no Portal com um perfil administrativo. "
                "A página que você tentou acessar é exclusiva para candidatos do PSCT.",
            )
        else:
            messages.warning(
                self.request,
                "Você precisa fornecer suas credenciais de acesso para visualizar "
                "a página que você requisitou.",
            )
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = datetime.now()
        context["edicoes"] = (
            models_ps.Edicao.objects.filter(
                edital__processo_inscricao__isnull=False,
                edital__processo_inscricao__data_inicio__lte=now,
                edital__processo_inscricao__data_encerramento__gte=now,
            )
            .exclude(edital__inscricao__candidato__user=self.request.user)
            .distinct()
            .order_by("-ano", "-semestre")
        )
        context["inscricoes"] = (
            models_inscricao.Inscricao.objects.filter(
                candidato__user=self.request.user,
                edital__processo_inscricao__isnull=False,
            )
            .distinct()
            .order_by("-edital__edicao__ano", "-edital__edicao__semestre")
        )
        context["titulo"] = "Minhas Inscrições"
        return context


class PreCadastroCandidatoFormView(generic.FormView):
    form_class = forms.PreCadastroCandidatoForm
    template_name = "psct/pre_cadastro_candidato.html"

    def get_success_url(self):
        url = reverse("dados_basicos_psct")

        cpf = self.request.POST.get("cpf", None)
        if cpf:
            url = f"{url}?cpf={cpf}"

        query_str = self.request.META.get("QUERY_STRING", None)
        if cpf and query_str:
            url = f"{url}&{query_str}"
        elif query_str:
            url = f"{url}?{query_str}"

        return url

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Novo Cadastro"
        data["nome_botao"] = "Continuar"
        data["breadcrumb"] = BreadCrumb.create(("Novo Cadastro", ""))
        return data


@method_decorator(sensitive_post_parameters("password", "password_confirm"), "dispatch")
class CandidatoView(RevisionMixin, generic.FormView):
    form_class = forms.CandidatoCadastroForm
    template_name = "psct/dados_basicos.html"

    def get_initial(self):
        initial = super().get_initial()
        cpf = self.request.GET.get("cpf", None)
        if cpf:
            initial.update({"cpf": cpf})
        return initial

    def form_valid(self, form):
        form.save()

        username = form.instance.user.username
        password = form.cleaned_data["password"]
        auth_user = auth.authenticate(username=username, password=password)

        next = self.request.GET.get("next")

        if auth_user is not None:
            auth.login(self.request, auth_user)
            messages.success(self.request, "Cadastro realizado com sucesso.")
            return redirect(next or reverse("index_psct"))

        messages.warning(
            self.request, "Realize o login para continuar a inscrição no PSCT."
        )
        return redirect("candidato_login")

    def get(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            candidato = get_object_or_permission_denied(
                models.Candidato, user=self.request.user
            )
            next = self.request.GET.get("next")
            if next:
                return redirect(
                    reverse("dados_basicos_update_psct", args=[candidato.id])
                    + "?next="
                    + next
                )
            return redirect(reverse("dados_basicos_update_psct", args=[candidato.id]))
        return super().get(request, *args, **kwargs)

    def form_invalid(self, form):
        if "declara_veracidade" in form.data:
            new_data = form.data.copy()
            new_data["declara_veracidade"] = False
            form.data = new_data
        return super().form_invalid(form)


@method_decorator(sensitive_post_parameters("password", "password_confirm"), "dispatch")
class CandidatoUpdateView(RevisionMixin, LoginRequiredMixin, generic.UpdateView):
    model = models.Candidato
    form_class = forms.CandidatoForm
    template_name = "psct/dados_basicos_update.html"

    def get_object(self, queryset=None):
        return get_object_or_permission_denied(
            models.Candidato, pk=int(self.kwargs["pk"]), user=self.request.user
        )

    def get_success_url(self):
        next = self.request.GET.get("next")
        messages.success(self.request, "Dados básicos foram salvos com sucesso.")
        return next or reverse("dados_basicos_update_psct", args=[self.object.id])

    def form_invalid(self, form):
        if "declara_veracidade" in form.data:
            new_data = form.data.copy()
            new_data["declara_veracidade"] = False
            form.data = new_data
        return super().form_invalid(form)


class CandidatoDadosBasicosRedirectView(GroupRequiredMixin, generic.RedirectView):
    group_required = ["Candidatos", "Candidatos PSCT"]

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if permissions.CandidatosPSCT.has_member(user):
            return reverse("dados_basicos_psct")
        return reverse("dados_basicos_candidato")


class CandidatoImportarSISU(RevisionMixin, GroupRequiredMixin, generic.FormView):
    template_name = "psct/base/confirmacao.html"
    group_required = "Administradores PSCT"
    form_class = forms.ImportarSISUForm

    def get_success_url(self):
        return reverse("admin:psct_candidato_changelist")

    def form_valid(self, form):
        models.importar_candidato_sisu(form.cleaned_data["cpf"])
        messages.success(self.request, "Candidato importado com sucesso!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Importar candidato SISU"
        data["nome_botao"] = "Importar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Candidatos", self.get_success_url()), ("Importar candidato SISU", "")
        )
        data["back_url"] = self.get_success_url()
        return data
