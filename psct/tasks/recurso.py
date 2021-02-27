import tempfile

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.lookups import Unaccent
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models.functions import Upper
from django.template.loader import render_to_string
from django.urls import reverse

from monitoring.models import PortalTask
from psct import pdf
from psct.distribuicao import recurso as distribuicao
from psct.models import recurso as models
from psct.models.consulta import Coluna


@shared_task(name="Distribuir Recursos PSCT", base=PortalTask)
def distribuir_recursos(fase_id, coluna_id, avaliadores, homologadores):
    coluna = Coluna.objects.get(id=coluna_id)
    fase = models.FaseRecurso.objects.get(id=fase_id)
    with transaction.atomic():
        distribuicao.DistribuidorGrupoAvaliadores(fase, coluna, avaliadores).executar()
        avaliadores = models.Group.objects.get(name="Avaliador PSCT")
        for mb in models.MailBoxAvaliador.objects.filter(fase=fase):
            mb.avaliador.groups.add(avaliadores)

        if fase.requer_homologador:
            distribuicao.DistribuidorGrupoHomologadores(
                fase, coluna, homologadores
            ).executar()
            homologadores = models.Group.objects.get(name="Homologador PSCT")
            for mb in models.MailBoxHomologador.objects.filter(fase=fase):
                mb.homologador.groups.add(homologadores)

    return {
        "url": reverse("list_recurso_psct"),
        "message": "Recursos distribuídos com sucesso!",
    }


@shared_task(ignore_result=True)
def generate_resultado_recursos_pdf(user_id, fase_pk):
    user = User.objects.get(id=user_id)

    fase = models.FaseRecurso.objects.get(pk=fase_pk)
    recursos = (
        fase.recurso_set.all()
        .annotate(nome_normalizado=Upper(Unaccent("inscricao__candidato__nome")))
        .distinct()
        .order_by("nome_normalizado")
    )

    filename = tempfile.mktemp(prefix="resultado_recursos", suffix=".pdf")

    with open(filename, "wb") as f:
        f.write(pdf.resultado_recursos_pdf(fase, recursos))

    assunto = "[Portal do Estudante] PDF - Resultado de Recursos"
    mensagem = render_to_string(
        "psct/mails/resultado_recursos.html", dict(user=user, fase=fase)
    )

    email = EmailMessage(
        assunto,
        mensagem,
        settings.EMAIL_FROM,
        [user.email],
        reply_to=[settings.EMAIL_REPLY_TO],
    )
    email.attach_file(filename)
    if settings.DEBUG:
        print(filename)
    email.send()
