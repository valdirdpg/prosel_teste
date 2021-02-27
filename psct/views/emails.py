from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic

from psct.forms.emails import ConfirmacaoForm
from psct.models.emails import Email, SolicitacaoEnvioEmail
from psct.tasks.emails import enviar_email


class SolicitacaoEmailView(PermissionRequiredMixin, generic.FormView):
    template_name = "psct/emails/envio_email.html"
    form_class = ConfirmacaoForm
    raise_exception = True
    permission_required = "psct.send_mail"

    def get_context_data(self, **kwargs):
        data = super().get_context_data()
        data["email"] = get_object_or_404(Email, pk=self.kwargs["pk"])
        return data

    def form_valid(self, form):
        email = Email.objects.get(id=self.kwargs["pk"])
        if form.cleaned_data["aceite"] == "1":
            solicitacao = SolicitacaoEnvioEmail.objects.create(
                email=email, usuario=self.request.user
            )
            enviar_email.delay(solicitacao.id)
            messages.info(self.request, "Seu email está sendo enviado!")
            return super().form_valid(form)
        else:
            messages.warning(self.request, "Você cancelou o envio do email!")
            return super().form_valid(form)

    def get_success_url(self):
        return reverse("admin:psct_email_changelist")
