from django.contrib.auth.models import User
from django.db import models

from psct.models.consulta import Consulta


class Email(models.Model):
    assunto = models.CharField(max_length=255, verbose_name="Assunto")
    conteudo = models.TextField(verbose_name="Conteúdo")
    destinatarios = models.ForeignKey(
        Consulta, verbose_name="Destinatários", on_delete=models.PROTECT
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True, verbose_name="Data da criação"
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Data da atualização"
    )

    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Emails"
        permissions = (("send_mail", "Administrador Pode Enviar Email"),)

    def __str__(self):
        return self.assunto


class SolicitacaoEnvioEmail(models.Model):
    email = models.ForeignKey(Email, verbose_name="email", on_delete=models.PROTECT)
    usuario = models.ForeignKey(User, verbose_name="Usuário", on_delete=models.PROTECT)
    data = models.DateTimeField(auto_now_add=True, verbose_name="Data da solicitação")
    sucesso = models.BooleanField(verbose_name="Sucesso?", default=False)

    class Meta:
        verbose_name_plural = "Solicitações de Envio de Email"
        verbose_name = "Solicitação de Envio de Email"

    def __str__(self):
        return self.email.assunto
