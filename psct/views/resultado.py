from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import generic

from base.custom.datatypes import BreadCrumb
from base.custom.views.mixin import GroupRequiredMixin
from cursos.models import Campus
from monitoring.models import Job
from psct.forms import resultado as resultado_forms
from psct.models import resultado as models
from psct.models.analise import FaseAnalise
from psct.models.inscricao import Inscricao
from psct.tasks import resultado as tasks


class ResultadoPreliminarView(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/base/confirmacao.html"
    form_class = forms.Form

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.fase = get_object_or_404(FaseAnalise, pk=self.kwargs["fase_pk"])

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["back_url"] = self.success_url
        data["titulo"] = f"Deseja gerar o resultado preliminar do {self.fase.edital}?"
        data["nome_botao"] = "Confirmar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Admin", reverse("admin:index")),
            ("PSCT", reverse("admin:app_list", args=["psct"])),
            ("Fases de análise", self.success_url),
            ("Gerar resultado preliminar", ""),
        )
        return data

    def form_valid(self, form):
        if self.fase.edital.processo_inscricao.possui_segunda_opcao:
            worker = tasks.gerar_resultado_preliminar_segunda_opcao
        else:
            worker = tasks.gerar_resultado_preliminar
        async_result = worker.delay(self.kwargs["fase_pk"])
        self.job = Job.new(
            self.request.user, async_result, name=tasks.gerar_resultado_preliminar.name
        )
        messages.info(
            self.request,
            "Sua solicitação está sendo processada."
            " Esta operação pode demorar alguns minutos.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return self.job.get_absolute_url()


class ResultadoFileView(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/base/confirmacao.html"
    form_class = resultado_forms.FileFormatForm
    success_url = reverse_lazy("admin:psct_resultadopreliminar_changelist")

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.resultado = get_object_or_404(
            models.ResultadoPreliminar, pk=self.kwargs["resultado_pk"]
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["back_url"] = self.success_url
        data["titulo"] = "Deseja exportar para arquivo o resultado do {}?".format(
            self.resultado.fase.edital
        )
        data["nome_botao"] = "Confirmar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Admin", reverse("admin:index")),
            ("PSCT", reverse("admin:app_list", args=["psct"])),
            ("Resultado Preliminar", self.success_url),
            ("Gerar resultado preliminar", ""),
        )
        return data

    def form_valid(self, form):
        render = form.cleaned_data["render"]
        filetype = form.cleaned_data["filetype"]
        tasks.exportar_resultado_arquivo.delay(
            self.request.user.id, self.resultado.id, render, filetype
        )
        messages.info(
            self.request,
            "Sua solicitação está sendo processada. Você receberá os arquivos por e-mail.",
        )
        return super().form_valid(form)


class GenericCreateResultadoView(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/base/confirmacao.html"
    form_class = forms.Form
    success_url = reverse_lazy("admin:psct_resultadopreliminar_changelist")
    model = None
    reverse_field_name = None
    success_message = None
    breadcrumb_title = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.resultado = get_object_or_404(
            models.ResultadoPreliminar, pk=self.kwargs["pk"]
        )

    def has_permission(self):
        perm = super().has_permission()
        return perm and hasattr(self.resultado.fase.edital, self.reverse_field_name)

    def get_title(self):
        return ""

    def get_extra_message(self):
        return ""

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["back_url"] = self.success_url
        data["titulo"] = self.get_title()
        data["extra_message"] = self.get_extra_message()
        data["nome_botao"] = "Confirmar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Admin", reverse("admin:index")),
            ("PSCT", reverse("admin:app_list", args=["psct"])),
            ("Resultado Preliminar", self.success_url),
            (self.breadcrumb_title, ""),
        )
        return data

    def form_valid(self, form):
        self.model.objects.create(
            resultado=self.resultado, edital=self.resultado.fase.edital
        )
        messages.success(self.request, self.success_message)
        return super().form_valid(form)


class GenericDeleteResultadoView(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/base/confirmacao.html"
    form_class = forms.Form
    success_url = reverse_lazy("admin:psct_resultadopreliminar_changelist")
    model = None
    reverse_field_name = None
    success_message = None
    breadcrumb_title = None

    def get_title(self):
        return ""

    def get_extra_message(self):
        return ""

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.resultado = get_object_or_404(
            models.ResultadoPreliminar, pk=self.kwargs["pk"]
        )

    def has_permission(self):
        perm = super().has_permission()
        return perm and hasattr(self.resultado.fase.edital, self.reverse_field_name)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["back_url"] = self.success_url
        data["titulo"] = self.get_title()
        data["extra_message"] = self.get_extra_message()
        data["nome_botao"] = "Confirmar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Admin", reverse("admin:index")),
            ("PSCT", reverse("admin:app_list", args=["psct"])),
            ("Resultado Preliminar", self.success_url),
            (self.breadcrumb_title, ""),
        )
        return data

    def form_valid(self, form):
        self.model.objects.filter(
            resultado=self.resultado, edital=self.resultado.fase.edital
        ).delete()
        messages.success(self.request, self.success_message)
        return super().form_valid(form)


class HomologarResultadoPreliminarView(GenericCreateResultadoView):
    reverse_field_name = "resultado_preliminar"
    model = models.ResultadoPreliminarHomologado
    breadcrumb_title = "Definir resultado preliminar"
    success_message = "Resultado preliminar definido com sucesso."

    def get_title(self):
        return f"Definir resultado preliminar do {self.resultado.fase.edital}"

    def get_extra_message(self):
        return "Deseja realmente definir o {} oficialmente como resultado preliminar do {}?".format(
            self.resultado, self.resultado.fase.edital
        )


class RemoverHomologacaoResultadoPreliminarView(GenericDeleteResultadoView):
    reverse_field_name = "resultado_preliminar"
    model = models.ResultadoPreliminarHomologado
    breadcrumb_title = "Remover resultado preliminar"
    success_message = "Resultado preliminar removido com sucesso."

    def get_title(self):
        return "Remover a homologação do resultado preliminar do {}".format(
            self.resultado.fase.edital
        )

    def get_extra_message(self):
        return "Deseja realmente remover o resultado preliminar do {}?".format(
            self.resultado.fase.edital
        )


class CreateResultadoView(GenericCreateResultadoView):
    reverse_field_name = "resultado"
    model = models.ResultadoFinal
    breadcrumb_title = "Definir resultado"
    success_message = "Resultado definido com sucesso."

    def get_title(self):
        return f"Definir resultado do {self.resultado.fase.edital}"

    def get_extra_message(self):
        return "Deseja realmente definir o {} oficialmente como resultado do {}?".format(
            self.resultado, self.resultado.fase.edital
        )


class DeleteResultadoView(GenericDeleteResultadoView):
    reverse_field_name = "resultado"
    model = models.ResultadoFinal
    breadcrumb_title = "Remover resultado"
    success_message = "Resultado removido com sucesso."

    def get_title(self):
        return f"Remover o resultado do {self.resultado.fase.edital}"

    def get_extra_message(self):
        return f"Deseja realmente remover o resultado do {self.resultado.fase.edital}?"


class ResultadoInscricaoView(GroupRequiredMixin, generic.TemplateView):
    raise_exception = True
    group_required = "Candidatos PSCT"
    template_name = "psct/resultado/extrato.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.inscricao = get_object_or_404(Inscricao, pk=self.kwargs["pk"])

    def has_permission(self):
        perm = super().has_permission()
        return (
            perm and
            self.inscricao.pode_ver_resultado_preliminar and
            self.inscricao.is_owner(self.request.user)
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["inscricao"] = self.inscricao
        data["resultado"] = self.inscricao.get_resultado()
        data["situacao"] = self.inscricao.get_situacao()
        data["pontuacao"] = self.inscricao.get_extrato_pontuacao()
        data["breadcrumb"] = BreadCrumb.create(
            ("Minhas Inscrições", reverse("index_psct")),
            ("Extrato de Desempenho", "")
        )
        return data


class RodizioVagasView(GroupRequiredMixin, generic.TemplateView):
    raise_exception = True
    group_required = "Administradores PSCT"
    template_name = "psct/resultado/vagas.html"
    success_url = reverse_lazy("admin:psct_resultadopreliminar_changelist")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        resultado = get_object_or_404(models.ResultadoPreliminar, pk=self.kwargs["pk"])
        data["resultado"] = resultado
        data["breadcrumb"] = BreadCrumb.create(
            ("Admin", reverse("admin:index")),
            ("PSCT", reverse("admin:app_list", args=["psct"])),
            ("Resultado Preliminar", self.success_url),
            ("Distribuição de Vagas", ""),
        )
        campi = []

        for campus in Campus.objects.filter(
                cursonocampus__cursoselecao__processoinscricao__edital=resultado.fase.edital
        ).distinct():
            campus_data = []
            for curso in resultado.fase.edital.processo_inscricao.cursos.filter(
                campus=campus
            ):
                curso_data = []
                qs = models.VagasResultadoPreliminar.objects.filter(
                    resultado_curso__resultado=resultado, resultado_curso__curso=curso
                ).order_by("modalidade")
                for v in qs:
                    curso_data.append([v.modalidade.resumo, v.quantidade])
                campus_data.append([curso, curso_data])
            campi.append([campus, campus_data])
        data["campi"] = campi
        return data
