import tempfile

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse

from cursos.models import Campus
from monitoring.models import PortalTask
from processoseletivo import models, pdf


@shared_task(base=PortalTask)
def importar_csv(edicao_id, user_id):
    edicao = models.Edicao.objects.get(id=edicao_id)
    user = User.objects.get(id=user_id)

    with transaction.atomic():
        edicao.importar()

    assunto = f"[Portal do Estudante] Importação de dados do {edicao}"
    mensagem = render_to_string(
        "processoseletivo/mails/importacao.html", dict(user=user, edicao=edicao)
    )

    email = EmailMessage(
        assunto,
        mensagem,
        settings.EMAIL_FROM,
        [user.email],
        reply_to=[settings.EMAIL_REPLY_TO],
    )
    email.send()

    return {
        "url": reverse("admin:processoseletivo_edicao_change", args=[edicao_id]),
        "message": "A importação foi realizada com sucesso!",
    }


@shared_task(ignore_result=True)
def relatorio_resultado_csv(edicao_id, user_id):
    edicao = models.Edicao.objects.get(id=edicao_id)
    user = User.objects.get(id=user_id)

    filename = edicao.exportar_dados()

    assunto = f"[Portal do Estudante] Relatório de Resultado do {edicao}"
    mensagem = render_to_string(
        "processoseletivo/mails/relatorio_resultado.html",
        dict(user=user, edicao=edicao),
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


@shared_task(ignore_result=True)
def gerar_chamada_ps(etapa_id, user_id):
    etapa = models.Etapa.objects.get(id=etapa_id)
    user = User.objects.get(id=user_id)

    etapa.gerar_chamadas()

    assunto = f"[Portal do Estudante] Geração de Chamadas da {etapa}"
    mensagem = render_to_string(
        "processoseletivo/mails/gerar_chamadas.html", dict(user=user, etapa=etapa)
    )

    email = EmailMessage(
        assunto,
        mensagem,
        settings.EMAIL_FROM,
        [user.email],
        reply_to=[settings.EMAIL_REPLY_TO],
    )

    email.send()


@shared_task(ignore_result=True)
def formulario_analise_documental_pdf(chamada_id, user_id):
    chamada = models.Chamada.objects.get(id=chamada_id)
    user = User.objects.get(id=user_id)
    pdf.FormulariosAnaliseDocumental(chamada, user).generate_files()


@shared_task(ignore_result=True)
def analise_documental_etapa_pdf(etapa_id, user_id):
    etapa = models.Etapa.objects.get(id=etapa_id)
    user = User.objects.get(id=user_id)
    queryset = models.Chamada.objects.filter(etapa=etapa).order_by(
        "curso__curso__nome", "modalidade"
    )

    prefix = "listagem_analise_documental_"
    anexos = (
        []
    )  # Lista de arquivos que serão adicionados como anexos no email a ser enviado

    if etapa.campus:
        filename = tempfile.mktemp(prefix=prefix, suffix=".pdf")
        with open(filename, "wb") as f:
            f.write(pdf.imprimir_lista_analise_documental(etapa, queryset))
        anexos.append(filename)
    else:
        # Cria as listas agrupadas por Campus
        for campus in Campus.objects.filter(
            cursonocampus__chamada__etapa=etapa
        ).distinct():
            queryset_campus = queryset.filter(curso__campus=campus)

            prefix_campus = f"campus_{campus.sigla.lower()}_{prefix}"
            filename = tempfile.mktemp(prefix=prefix_campus, suffix=".pdf")

            with open(filename, "wb") as f:
                f.write(
                    pdf.imprimir_lista_analise_documental(
                        etapa, queryset_campus, campus=campus
                    )
                )

            anexos.append(filename)

    assunto = f"[Portal do Estudante] Análise documental do {etapa}"
    mensagem = render_to_string(
        "processoseletivo/mails/analise_documental_etapa.html",
        dict(user=user, etapa=etapa),
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


@shared_task(ignore_result=True)
def gerar_listagem_final_deferidos_pdf(etapa_id, user_id):
    etapa = models.Etapa.objects.get(id=etapa_id)
    user = User.objects.get(id=user_id)
    pdf.RelatorioFinalDeferidos(etapa, user).generate_files()


@shared_task(ignore_result=True)
def gerar_listagem_final_indeferidos_pdf(etapa_id, user_id):
    etapa = models.Etapa.objects.get(id=etapa_id)
    user = User.objects.get(id=user_id)
    pdf.RelatorioFinalIndeferidos(etapa, user).generate_files()


@shared_task(ignore_result=True)
def gerar_listagem_final_excedentes_pdf(etapa_id, user_id):
    etapa = models.Etapa.objects.get(id=etapa_id)
    user = User.objects.get(id=user_id)
    pdf.RelatorioFinalExcedentes(etapa, user).generate_files()


@shared_task(ignore_result=True)
def relatorio_matriculados_xlsx(etapa_id, user_id):
    etapa = models.Etapa.objects.get(id=etapa_id)
    user = User.objects.get(id=user_id)

    filename = etapa.exportar(matriculados=True)

    assunto = f"[Portal do Estudante] Relatório dos matriculados do {etapa}"
    mensagem = render_to_string(
        "processoseletivo/mails/relatorio_matriculados.html",
        dict(user=user, etapa=etapa),
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


@shared_task(ignore_result=True)
def relatorio_convocados_xlsx(etapa_id, user_id):
    etapa = models.Etapa.objects.get(id=etapa_id)
    user = User.objects.get(id=user_id)

    filename = etapa.exportar()

    assunto = f"[Portal do Estudante] Relatório dos convocados do {etapa}"
    mensagem = render_to_string(
        "processoseletivo/mails/relatorio_convocados.html", dict(user=user, etapa=etapa)
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


@shared_task(ignore_result=True)
def relatorio_convocados_por_cota_pdf(etapa_id, user_id):
    etapa = models.Etapa.objects.get(id=etapa_id)
    user = User.objects.get(id=user_id)
    pdf.RelatorioConvocadosPorCota(etapa, user).generate_files()


@shared_task(base=PortalTask)
def encerrar_etapa(etapa_id):
    message = "A etapa foi encerrada com sucesso!"
    etapa = models.Etapa.objects.get(id=etapa_id)
    try:
        etapa.encerrar()
    except models.Etapa.EncerrarEtapaError as e:
        message = ",".join(e.messages)
    return {
        "url": reverse("admin:processoseletivo_etapa_change", args=[etapa_id]),
        "message": message,
    }


@shared_task(base=PortalTask)
def reabrir_etapa(etapa_id):
    etapa = models.Etapa.objects.get(id=etapa_id)
    if etapa.pode_reabrir():
        etapa.reabrir()
        mensagem = "A etapa foi reaberta com sucesso!"
    else:
        mensagem = "A etapa não pode ser reaberta, pois existe outra etapa posterior ou a mesma não está encerrada."
    return {
        "url": reverse("admin:processoseletivo_etapa_change", args=[etapa_id]),
        "message": mensagem,
    }
