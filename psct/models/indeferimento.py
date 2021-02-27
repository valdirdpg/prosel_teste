import reversion
from django.contrib.auth import get_user_model
from django.db import models

from psct.models.analise import InscricaoPreAnalise, JustificativaIndeferimento
from psct.models.recurso import ModelDate


@reversion.register
class IndeferimentoEspecial(ModelDate):
    inscricao = models.OneToOneField(
        InscricaoPreAnalise,
        related_name="indeferimento_especial",
        verbose_name="Inscrição",
        on_delete=models.CASCADE,
    )
    motivo_indeferimento = models.ForeignKey(
        JustificativaIndeferimento,
        verbose_name="Motivo do Indeferimento",
        on_delete=models.CASCADE,
    )
    autor = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
