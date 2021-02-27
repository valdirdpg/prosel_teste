import time

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import send_mail

from psct.itertools import grouper
from psct.models.emails import SolicitacaoEnvioEmail

MAX_MAILS_PER_CHUNCK = 100


MENSAGEM_USUARIO = """
Prezado(a) {},

  Informamos que seu email foi enviado com sucesso.


"""


@shared_task
def enviar_email(solicitacao_id):
    solicitacao = SolicitacaoEnvioEmail.objects.get(id=solicitacao_id)
    queryset = solicitacao.email.destinatarios.consulta_queryset
    for list_emails in grouper(queryset, MAX_MAILS_PER_CHUNCK):
        emails = [l[0] for l in list_emails]
        email = EmailMessage(
            subject=solicitacao.email.assunto,
            body=solicitacao.email.conteudo,
            from_email=settings.EMAIL_FROM,
            to=[],
            bcc=emails,
        )
        email.send()
        time.sleep(10)

    send_mail(
        subject="Confirmação de envio de email",
        message=MENSAGEM_USUARIO.format(solicitacao.usuario.get_full_name()),
        from_email=settings.EMAIL_FROM,  # enviado ao admin do sistema, utiliza email válido
        recipient_list=[solicitacao.usuario.email],
    )
    solicitacao.sucesso = True
    solicitacao.save()
