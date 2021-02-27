from celery import shared_task
from django.db import transaction
from django.urls import reverse

from monitoring.models import PortalTask
from psct.models.analise import FaseAnalise, InscricaoPreAnalise, ProgressoAnalise


@shared_task(name="Importar Inscrições", base=PortalTask)
def importar(fase_id):
    fase = FaseAnalise.objects.get(id=fase_id)
    with transaction.atomic():
        InscricaoPreAnalise.create_many(fase)
        objs = []
        for curso_edital in fase.edital.cursoedital_set.all():
            for vaga in curso_edital.modalidades.all():
                meta = vaga.quantidade_vagas * vaga.multiplicador
                if meta:
                    objs.append(
                        ProgressoAnalise(
                            fase=fase,
                            curso=curso_edital.curso,
                            modalidade=vaga.modalidade,
                            meta=meta,
                        )
                    )

        ProgressoAnalise.objects.bulk_create(objs)

    return {
        "url": reverse("list_inscricao_psct"),
        "message": "Importação realizada com sucesso!",
    }
