from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic
from reversion.views import RevisionMixin

from base.custom.datatypes import BreadCrumb
from base.custom.views.mixin import AnyGroupRequiredMixin
from base.shortcuts import get_object_or_permission_denied
from psct.forms.indeferimento import IndeferimentoEspecialForm
from psct.models import indeferimento as models
from psct.models.analise import SituacaoInscricao


class CreateIndeferimentoEspecialView(
    RevisionMixin, AnyGroupRequiredMixin, generic.CreateView
):
    model = models.IndeferimentoEspecial
    group_required = ("Homologador PSCT", "Administradores PSCT")
    raise_exception = True
    form_class = IndeferimentoEspecialForm
    template_name = "psct/base/display_form.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.inscricao_pre_analise = get_object_or_permission_denied(
                models.InscricaoPreAnalise,
                pk=self.kwargs["inscricao_pk"],
                situacao=SituacaoInscricao.INDEFERIDA.name,
            )
            self.fase = self.inscricao_pre_analise.fase.get_fase_ajuste()
            self.inscricao_original = self.inscricao_pre_analise.inscricao
            return self.fase.acontecendo and (
                self.fase.homologadores.grupo.user_set.filter(
                    id=self.request.user.id
                ).exists()
                or self.request.user.groups.filter(name="Administradores PSCT").exists()
            )

        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data[
            "titulo"
        ] = f"Adicionar indeferimento especial em {self.inscricao_original}"
        data["nome_botao"] = "Salvar"
        data["inscricao"] = self.inscricao_pre_analise
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_pontuacao_inscricao_psct")),
            ("Adicionar indeferimento", ""),
        )
        return data

    def get_initial(self):
        return {"inscricao": self.inscricao_pre_analise, "autor": self.request.user}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["inscricao"] = self.inscricao_pre_analise
        return kwargs

    def get_success_url(self):
        messages.info(self.request, "Indeferimento salvo com sucesso.")
        return reverse("list_pontuacao_inscricao_psct")

    def form_invalid(self, form):
        messages.error(
            self.request, "Por favor, corrija os erros abaixo para continuar."
        )
        return super().form_invalid(form)


class UpdateIndeferimentoEspecialView(
    RevisionMixin, AnyGroupRequiredMixin, generic.UpdateView
):
    model = models.IndeferimentoEspecial
    group_required = ("Homologador PSCT", "Administradores PSCT")
    raise_exception = True
    form_class = IndeferimentoEspecialForm
    template_name = "psct/base/display_form.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            object = self.get_object()
            self.inscricao_pre_analise = object.inscricao
            self.fase = self.inscricao_pre_analise.fase.get_fase_ajuste()
            return self.fase.acontecendo and (
                self.fase.homologadores.grupo.user_set.filter(
                    id=self.request.user.id
                ).exists()
                or self.request.user.groups.filter(name="Administradores PSCT").exists()
            )

        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data[
            "titulo"
        ] = f"Alterar indeferimento especial em {self.inscricao_pre_analise}"
        data["nome_botao"] = "Salvar"
        data["inscricao"] = self.inscricao_pre_analise
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_pontuacao_inscricao_psct")),
            ("Alterar indeferimento", ""),
        )
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["inscricao"] = self.inscricao_pre_analise
        return kwargs

    def get_success_url(self):
        messages.info(self.request, "Indeferimento salvo com sucesso.")
        return reverse("list_pontuacao_inscricao_psct")

    def form_invalid(self, form):
        messages.error(
            self.request, "Por favor, corrija os erros abaixo para continuar."
        )
        return super().form_invalid(form)


class DeleteIndeferimentoEspecialView(
    RevisionMixin, AnyGroupRequiredMixin, generic.FormView
):
    model = models.IndeferimentoEspecial
    group_required = ("Homologador PSCT", "Administradores PSCT")
    raise_exception = True
    template_name = "psct/base/confirmacao.html"
    form_class = forms.Form

    def get_object(self):
        self.object = get_object_or_404(self.model, pk=self.kwargs["pk"])
        return self.object

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            object = self.get_object()
            self.inscricao_pre_analise = object.inscricao
            self.fase = self.inscricao_pre_analise.fase.get_fase_ajuste()
            return self.fase.acontecendo and (
                self.fase.homologadores.grupo.user_set.filter(
                    id=self.request.user.id
                ).exists()
                or self.request.user.groups.filter(name="Administradores PSCT").exists()
            )

        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data[
            "titulo"
        ] = f"Remover indeferimento especial em {self.inscricao_pre_analise}"
        data["extra_message"] = (
            f'Deseja realmente remover o indeferimento "{self.object.motivo_indeferimento}" '
            f"de {self.inscricao_pre_analise}?"
        )
        data["nome_botao"] = "Remover"
        data["inscricao"] = self.inscricao_pre_analise
        data["back_url"] = reverse("list_pontuacao_inscricao_psct")
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", data["back_url"]), ("Remover indeferimento", "")
        )
        return data

    def get_success_url(self):
        messages.info(self.request, "Indeferimento removido com sucesso.")
        return reverse("list_pontuacao_inscricao_psct")

    def form_valid(self, form):
        self.object.delete()
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "Por favor, corrija os erros abaixo para continuar."
        )
        return super().form_invalid(form)
