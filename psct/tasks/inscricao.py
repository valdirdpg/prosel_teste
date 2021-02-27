import tempfile

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.lookups import Unaccent
from django.core.mail import EmailMessage
from django.db.models.functions import Upper
from django.template.loader import render_to_string

from cursos.models import Campus
from editais.models import Edital
from psct import pdf


@shared_task(ignore_result=True)
def generate_pdf(user_id, edital_pk, lista_final=False):
    user = User.objects.get(id=user_id)

    edital = Edital.objects.get(pk=edital_pk)
    inscricoes = (
        edital.inscricao_set.filter(
            aceite=True, cancelamento__isnull=True, comprovantes__isnull=False
        )
        .annotate(nome_normalizado=Upper(Unaccent("candidato__nome")))
        .distinct()
        .order_by("nome_normalizado")
    )

    tipo_lista = "final" if lista_final else "preliminar"

    anexos = (
        []
    )  # Lista de arquivos que serão adicionados como anexos no email a ser enviado

    # Cria a lista geral de candidatos inscritos
    prefix = f"lista_{tipo_lista}_geral"
    filename = tempfile.mktemp(prefix=prefix, suffix=".pdf")

    with open(filename, "wb") as f:
        f.write(pdf.lista_inscritos_pdf(edital, inscricoes, final=lista_final))

    anexos.append(filename)

    # Cria as listas de candidatos inscritos agrupadas por Campi
    for campus in Campus.objects.filter(
        cursonocampus__cursoselecao__processoinscricao__edital=edital
    ).distinct():
        queryset_campus = inscricoes.filter(curso__campus=campus)

        prefix = f"lista_{tipo_lista}_{campus.sigla.lower()}_"
        filename = tempfile.mktemp(prefix=prefix, suffix=".pdf")

        with open(filename, "wb") as f:
            f.write(
                pdf.lista_inscritos_pdf(
                    edital, queryset_campus, final=lista_final, campus=campus
                )
            )

        anexos.append(filename)

    assunto = f"[Portal do Estudante] PDF - Relação {tipo_lista} de inscritos"
    mensagem = render_to_string(
        "psct/mails/lista_inscritos.html", dict(user=user, tipo_lista=tipo_lista)
    )

    email = EmailMessage(
        assunto,
        mensagem,
        settings.EMAIL_FROM,
        [user.email],
        reply_to=[settings.EMAIL_REPLY_TO],
    )
    for a in anexos:
        email.attach_file(a)

        if settings.DEBUG:
            print(a)

    email.send()
