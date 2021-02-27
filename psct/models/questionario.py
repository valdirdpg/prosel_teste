from datetime import datetime

import reversion
from django.db import models

from editais.models import Edital
from psct.models import Inscricao
from psct.models.candidato import Candidato


@reversion.register
class CriterioQuestionario(models.Model):
    numero = models.PositiveSmallIntegerField(verbose_name="Número da questão")
    descricao_questao = models.TextField("Descrição do Critério/Questão")
    multipla_escolha = models.BooleanField("Permite múltipla escolha", default=False)

    class Meta:
        verbose_name = "Critério de Questionário"
        verbose_name_plural = "Critérios de Questionário"
        ordering = ("numero",)

    def __str__(self):
        return f"{self.numero} - {self.descricao_questao}"


@reversion.register
class CriterioAlternativa(models.Model):
    posicao = models.PositiveSmallIntegerField(
        verbose_name="Posição da alternativa na questão"
    )
    criterio = models.ForeignKey("psct.CriterioQuestionario", on_delete=models.CASCADE)
    descricao_alternativa = models.TextField("Alternativa")

    class Meta:
        verbose_name = "Alternativa"
        verbose_name_plural = "Alternativas"
        ordering = ("posicao",)

    def __str__(self):
        return f"{self.posicao} - {self.descricao_alternativa}"


@reversion.register
class ModeloQuestionario(models.Model):
    edital = models.OneToOneField(
        Edital, verbose_name="edital", on_delete=models.PROTECT
    )
    nome = models.CharField(
        "Descrição do Modelo de Questionário", max_length=255, unique=True
    )
    itens_avaliados = models.ManyToManyField(
        "psct.CriterioQuestionario", verbose_name="Critérios do questionário"
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Modelo de Questionário"
        verbose_name_plural = "Modelos de Questionários"

    @property
    def em_periodo_inscricao(self):
        processo = self.edital.processo_inscricao
        return (
            processo.data_inicio <= datetime.now().date() <= processo.data_encerramento
        )

@reversion.register
class RespostaModelo(models.Model):
    modelo = models.ForeignKey(
        ModeloQuestionario, verbose_name="modelo", on_delete=models.PROTECT
    )
    candidato = models.ForeignKey(
        Candidato, verbose_name="candidato", on_delete=models.PROTECT
    )

    class Meta:
        verbose_name = "Questionário Respondido"
        verbose_name_plural = "Questionários Respondidos"

    def is_owner(self, user):
        try:
            candidato = Candidato.objects.get(user=user)
            return candidato == self.candidato
        except Candidato.DoesNotExist:
            return False

@reversion.register
class RespostaCriterio(models.Model):
    resposta_modelo = models.ForeignKey(
        RespostaModelo, verbose_name="Resposta do Modelo", on_delete=models.PROTECT
    )
    criterio_alternativa_selecionada = models.ForeignKey(
        "psct.CriterioAlternativa", on_delete=models.PROTECT
    )

    def is_owner(self, user):
        try:
            candidato = Candidato.objects.get(user=user)
            return candidato == self.candidato
        except Candidato.DoesNotExist:
            return False