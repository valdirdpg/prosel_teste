import tempfile

import xlsxwriter
from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from psct.models.consulta import Consulta

MAX_CHARS_BY_SHEET_NAME = 30


@shared_task(ignore_result=True)
def generate_xls(user_id, consulta_id):
    user = User.objects.get(id=user_id)
    consulta = Consulta.objects.get(id=consulta_id)

    filename = tempfile.mktemp(suffix=".xls")
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet(consulta.nome[:MAX_CHARS_BY_SHEET_NAME])
    worksheet.write_row(0, 0, [str(col.nome) for col in consulta.colunas_label])
    index = 1
    for tupla in consulta.consulta_queryset:
        worksheet.write_row(index, 0, tupla)
        index += 1
    workbook.close()

    assunto = f"[Portal do Estudante] XLS - Consulta {consulta.nome}"
    mensagem = render_to_string(
        "psct/mails/consulta_xls.html", dict(user=user, consulta=consulta)
    )

    email = EmailMessage(
        assunto,
        mensagem,
        settings.EMAIL_FROM,
        [user.email],
        reply_to=[settings.EMAIL_REPLY_TO],
    )
    email.attach_file(filename)

    email.send()
    if settings.DEBUG:
        print(filename)
