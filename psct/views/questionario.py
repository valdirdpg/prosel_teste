from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
from reversion.views import RevisionMixin

from base.shortcuts import get_object_or_permission_denied
from psct.forms.questionario import ResponderQuestionarioForm
from psct.models import inscricao as models_inscricao
from psct.models import questionario as models


class QuestionarioCreate(RevisionMixin, UserPassesTestMixin, generic.FormView):
    form_class = ResponderQuestionarioForm
    template_name = "psct/responder_questionario.html"

    def test_func(self):
        user = self.request.user
        if user.is_authenticated and self.modelo.em_periodo_inscricao:
            return True
        else:
            return False

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            now = datetime.now().date()
            self.edital = get_object_or_permission_denied(
                models.Edital,
                pk=self.kwargs["edital_pk"],
                processo_inscricao__isnull=False,
                processo_inscricao__data_inicio__lte=now,
                processo_inscricao__data_encerramento__gte=now,
            )
            try:
                self.modelo = self.edital.modeloquestionario
            except models.ModeloQuestionario.DoesNotExist:
                raise Http404()
            self.candidato = get_object_or_permission_denied(
                models.Candidato, user=self.request.user
            )
            if not self.candidato.is_atualizado_recentemente():
                messages.info(
                    self.request,
                    "Primeiramente, atualize os seus dados de cadastro e "
                    "clique no botão de Salvar no final da página.",
                )
                return redirect(
                    reverse("dados_basicos_psct")
                    + "?next="
                    + reverse("responder_questionario_psct", args=[self.edital.id])
                )

            inscricao = models_inscricao.Inscricao.objects.filter(
                candidato=self.candidato, edital=self.edital
            ).first()
            if inscricao and inscricao.is_cancelada:
                messages.error(
                    self.request,
                    f"Você precisa desfazer o cancelamento da inscrição em {inscricao.edital.edicao} - "
                    f"Edital nº {inscricao.edital.numero}/{inscricao.edital.ano} para continuar editando.",
                )
                return redirect("index_psct")
            active = self.request.GET.get("active")
            if self.candidato.has_inscricao() and not active:
                messages.error(
                    self.request,
                    f"Somente é possível se inscrever para uma única forma (integrado, subsequente ou concomitante). Caso deseje alterar, cancele a inscrição anterior e faça uma nova.",
                )
                return redirect("index_psct")

            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["modelo"] = self.modelo
        kwargs["candidato"] = self.candidato
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["edital"] = self.modelo.edital
        context["back_url"] = reverse("dados_basicos_psct") + "?next=" + reverse("responder_questionario_psct", args=[self.edital.id]) + "?active=OK"

        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("create_inscricao_psct", kwargs=dict(edital_pk=self.edital.id))
