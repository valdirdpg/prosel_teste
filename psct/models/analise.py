import operator
from datetime import datetime
from functools import reduce

import reversion
from django.apps import apps
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db import transaction
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.db.models.signals import post_save
from django.dispatch import receiver

from base.choices import BaseChoice
from base.utils import exists
from cursos.models import CursoSelecao
from editais.models import Edital
from psct.models.candidato import Candidato
from psct.models.consulta import Coluna
from psct.models.inscricao import Inscricao, Modalidade, ModalidadeVagaCursoEdital, ZERO
from psct.models.recurso import GrupoEdital, ModelDate


@reversion.register()
class FaseAnalise(ModelDate):
    nome = models.CharField(verbose_name="Nome da Fase", max_length=255)
    edital = models.ForeignKey(Edital, verbose_name="Edital", on_delete=models.PROTECT)
    data_inicio = models.DateTimeField(verbose_name="Data de Início")
    data_encerramento = models.DateTimeField(verbose_name="Data de encerramento")
    data_resultado = models.DateTimeField(
        verbose_name="Data de divulgação do resultado"
    )
    quantidade_avaliadores = models.PositiveSmallIntegerField(
        verbose_name="Quantidade de Avaliadores", default=2
    )
    requer_homologador = models.BooleanField(
        verbose_name="Requer homologador?", default=True
    )
    avaliadores = models.ForeignKey(
        GrupoEdital,
        verbose_name="Grupo de Avaliadores",
        related_name="fase_analise_avaliadores",
        on_delete=models.PROTECT,
    )
    homologadores = models.ForeignKey(
        GrupoEdital,
        verbose_name="Grupo de Homologadores",
        related_name="fase_analise_homologadores",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "Fase de Análise"
        verbose_name_plural = "Fases de Análise"

    def __str__(self):
        return f"{self.nome} - Edital {self.edital.numero}/{self.edital.ano}"

    @property
    def acontecendo(self):
        return self.data_inicio <= datetime.now() <= self.data_encerramento

    def clean(self):
        if (
            exists(self.data_encerramento, self.data_inicio)
            and self.data_encerramento < self.data_inicio
        ):
            raise ValidationError(
                {
                    "data_encerramento": "A data de encerramento não pode ser inferior ao seu início"
                }
            )
        if (
            exists(self.data_resultado, self.data_encerramento)
            and self.data_resultado <= self.data_encerramento
        ):
            raise ValidationError(
                {
                    "data_resultado": (
                        "A data de divulgação do resultado não pode ser inferior ao encerramento "
                        "do período de análise"
                    )
                }
            )
        if (
            exists(self.data_inicio, self.edital_id)
            and self.data_inicio.date()
            <= self.edital.processo_inscricao.data_encerramento
        ):
            raise ValidationError(
                {
                    "data_inicio": "A fase de análise só pode começar após o encerramento das inscrições"
                }
            )

        if (
            exists(self.avaliadores_id, self.edital_id)
            and self.avaliadores.edital != self.edital
        ):
            raise ValidationError(
                {
                    "avaliadores": "O grupo de avaliadores não pertence ao edital selecionado"
                }
            )

        if (
            exists(self.homologadores_id, self.edital_id)
            and self.homologadores.edital != self.edital
        ):
            raise ValidationError(
                {
                    "homologadores": "O grupo de homologadores não pertence ao edital selecionado"
                }
            )

        if self.requer_homologador and not exists(self.homologadores_id):
            raise ValidationError(
                {"homologadores": "O grupo de homologadores não foi definido"}
            )

        if exists(self.avaliadores_id, self.homologadores_id):
            h_users = set(self.homologadores.grupo.user_set.all())
            users = set(self.avaliadores.grupo.user_set.all())
            if users & h_users:
                raise ValidationError(
                    "Existem membros do grupo de homologadores presentes no grupo de avaliação"
                )

            if len(users) < self.quantidade_avaliadores:
                raise ValidationError(
                    {
                        "avaliadores": "O Grupo de avaliadores tem menos usuários do que a fase exige de avaliadores"
                    }
                )

        if (
            exists(self.homologadores_id)
            and not self.homologadores.grupo.user_set.exists()
        ):
            raise ValidationError(
                {"homologadores": "O grupo de homologadores está vazio."}
            )

    def eh_avaliador(self, user):
        return self.avaliadores.grupo.user_set.filter(id=user.id).exists()

    def eh_homologador(self, user):
        return self.homologadores.grupo.user_set.filter(id=user.id).exists()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.atualizar_grupos_permissao()

    def atualizar_grupos_permissao(self):
        avaliadores = Group.objects.get(name="Avaliador PSCT")
        avaliadores.user_set.add(*self.avaliadores.grupo.user_set.all())

        if self.homologadores:
            homologadores = Group.objects.get(name="Homologador PSCT")
            homologadores.user_set.add(*self.homologadores.grupo.user_set.all())

    def get_resultado_preliminar(self):
        try:
            return self.resultado_preliminar
        except ObjectDoesNotExist:
            # utilizando a superclasse para evitar import circular
            return None

    def get_fase_ajuste(self):
        try:
            return self.ajuste_pontuacao
        except ObjectDoesNotExist:
            return None


class SituacaoInscricao(BaseChoice):
    SEM_AVALIADORES = "Sem Avaliadores"
    AVALIADOR_FALTANDO = "Avaliador faltando"
    AVALIACAO_PENDENTE = "Com Avaliação Pendente"
    AGUARDANDO_HOMOLOGADOR = "Aguardando Homologador"
    DEFERIDA = "Deferida"
    INDEFERIDA = "Indeferida"


class InscricaoPreAnalise(models.Model):
    fase = models.ForeignKey(
        FaseAnalise,
        verbose_name="Fase Análise",
        related_name="inscricoes",
        on_delete=models.PROTECT,
    )
    candidato = models.ForeignKey(
        Candidato, verbose_name="Candidato", on_delete=models.PROTECT
    )
    curso = models.ForeignKey(
        CursoSelecao,
        verbose_name="Curso",
        on_delete=models.PROTECT,
        related_name="inscricoes_preanalise",
    )
    curso_segunda_opcao = models.ForeignKey(
        CursoSelecao,
        verbose_name="Curso",
        on_delete=models.PROTECT,
        related_name="inscricao_preanalise_2a_opcao",
        null=True,
        blank=True,
    )
    modalidade = models.ForeignKey(
        Modalidade,
        verbose_name="Modalidade da Cota",
        default=1,
        on_delete=models.PROTECT,
    )
    pontuacao = models.DecimalField(
        verbose_name="Pontuação", max_digits=5, decimal_places=2, default=ZERO
    )
    pontuacao_pt = models.DecimalField(
        verbose_name="Valor de desempate PT",
        max_digits=5,
        decimal_places=2,
        default=ZERO,
    )
    pontuacao_mt = models.DecimalField(
        verbose_name="Valor de desempate MT",
        max_digits=5,
        decimal_places=2,
        default=ZERO,
    )
    nascimento = models.DateField(verbose_name="Data de Nascimento")
    situacao = models.CharField(
        verbose_name="Situação",
        choices=SituacaoInscricao.choices(blank=True),
        max_length=55,
    )

    @property
    def inscricao(self):
        return Inscricao.objects.get(edital=self.fase.edital, candidato=self.candidato)

    @property
    def avaliacao(self):
        return self.avaliacoes_homologador.first()

    def get_avaliadores(self):
        return [mb.avaliador for mb in self.mailbox_avaliadores.all()]

    def get_homologador(self):
        mb = self.mailbox_homologadores.first()
        if mb:
            return mb.homologador

    @property
    def deferida(self):
        return self.situacao == SituacaoInscricao.DEFERIDA.name

    @property
    def indeferida(self):
        return self.situacao == SituacaoInscricao.INDEFERIDA.name

    class Meta:
        verbose_name_plural = "Inscrições Pré-Análise"
        verbose_name = "Inscrição Pré-Análise"
        ordering = "-pontuacao", "-pontuacao_pt", "-pontuacao_mt", "nascimento"

    def __str__(self):
        return f"{self.candidato} - {self.curso}"

    @classmethod
    def create_from_raw_inscricao(cls, inscricao, fase):
        obj, created = cls.objects.get_or_create(
            fase=fase,
            candidato=inscricao.candidato,
            curso=inscricao.curso,
            modalidade=inscricao.modalidade_cota,
            pontuacao=inscricao.pontuacao.valor,
            pontuacao_pt=inscricao.pontuacao.valor_pt,
            pontuacao_mt=inscricao.pontuacao.valor_mt,
            nascimento=inscricao.candidato.nascimento,
            situacao=SituacaoInscricao.SEM_AVALIADORES.name,
        )
        return obj

    @classmethod
    def create_many(cls, fase):
        inscricoes = []
        for inscricao in Inscricao.validas.select_related(
            "pontuacao", "candidato"
        ).filter(edital=fase.edital):
            inscricoes.append(
                cls(
                    fase=fase,
                    candidato=inscricao.candidato,
                    curso=inscricao.curso,
                    curso_segunda_opcao=inscricao.curso_segunda_opcao,
                    modalidade=inscricao.modalidade_cota,
                    pontuacao=inscricao.pontuacao.valor,
                    pontuacao_pt=inscricao.pontuacao.valor_pt,
                    pontuacao_mt=inscricao.pontuacao.valor_mt,
                    nascimento=inscricao.candidato.nascimento,
                    situacao=SituacaoInscricao.SEM_AVALIADORES.name,
                )
            )
        cls.objects.bulk_create(inscricoes)

    def pode_empilhar(self, user, is_administrador=False):
        return (
            self.fase.get_fase_ajuste()
            and self.indeferida
            and not self.empilhada
            and (
                self.fase.eh_avaliador(user)
                or self.fase.eh_homologador(user)
                or is_administrador
            )
        )

    @property
    def empilhada(self):
        pilha_class = apps.get_model("psct", "pilhainscricaoajuste")
        return pilha_class.objects.filter(
            fase__fase_analise=self.fase, inscricoes=self
        ).exists()

    @property
    def motivo_indeferimento(self):
        if self.indeferida:
            if hasattr(self, "indeferimento_especial"):
                return self.indeferimento_especial.motivo_indeferimento
            avaliacao_homologador = self.avaliacoes_homologador.first()
            if avaliacao_homologador:
                return avaliacao_homologador.texto_indeferimento
            avaliacao_avaliador = self.avaliacoes_avaliador.first()
            if avaliacao_avaliador:
                return avaliacao_avaliador.texto_indeferimento


class MailBoxAvaliadorInscricao(models.Model):
    fase = models.ForeignKey(
        FaseAnalise,
        verbose_name="Fase de Análise",
        on_delete=models.PROTECT,
        related_name="mailbox_avaliadores",
    )
    inscricoes = models.ManyToManyField(
        InscricaoPreAnalise,
        verbose_name="Inscrições",
        related_name="mailbox_avaliadores",
    )
    avaliador = models.ForeignKey(
        User,
        verbose_name="Avaliador",
        on_delete=models.PROTECT,
        related_name="mailbox_avaliador_inscricao",
    )

    class Meta:
        verbose_name = "Caixa de Inscrições do Avaliador"
        verbose_name_plural = "Caixas de Inscrições dos Avaliadores"
        unique_together = ("fase", "avaliador")

    def __str__(self):
        return f"Caixa de Inscrições do Avaliador {self.avaliador}"

    def add(self, inscricao):
        self.inscricoes.add(inscricao)
        ProgressoAnalise.objects.filter(
            fase=self.fase, curso=inscricao.curso, modalidade=inscricao.modalidade
        ).update(em_analise=models.F("em_analise") + 1)

    @classmethod
    def possui_inscricao_pendente(cls, fase, avaliador):
        return cls.objects.filter(
            models.Q(
                inscricoes__avaliacoes_avaliador__avaliador=avaliador,
                inscricoes__avaliacoes_avaliador__concluida=Concluida.NAO.name,
            )
            | models.Q(inscricoes__isnull=False)
            & (~models.Q(inscricoes__avaliacoes_avaliador__avaliador=avaliador)),
            fase=fase,
            avaliador=avaliador,
        ).exists()


class MailBoxHomologadorInscricao(models.Model):
    fase = models.ForeignKey(
        FaseAnalise,
        verbose_name="Fase de Análise",
        on_delete=models.PROTECT,
        related_name="mailbox_homologadores",
    )
    inscricoes = models.ManyToManyField(
        InscricaoPreAnalise,
        verbose_name="Inscrições",
        related_name="mailbox_homologadores",
    )
    homologador = models.ForeignKey(
        User,
        verbose_name="Homologador",
        on_delete=models.PROTECT,
        related_name="mailbox_homologador_inscricao",
    )

    @classmethod
    def possui_inscricao_pendente(cls, fase, homologador):
        return cls.objects.filter(
            inscricoes__isnull=False,
            inscricoes__avaliacoes_homologador__isnull=True,
            fase=fase,
            homologador=homologador,
        ).exists()

    class Meta:
        verbose_name = "Caixa de Inscrições do Homologador"
        verbose_name_plural = "Caixas de Inscrições dos Homologadores"
        unique_together = ("fase", "homologador")

    def __str__(self):
        return f"Caixa de Inscrições do Homologador {self.homologador}"


@reversion.register()
class JustificativaIndeferimento(models.Model):
    edital = models.ForeignKey(Edital, verbose_name="Edital", on_delete=models.CASCADE)
    texto = models.TextField(verbose_name="Texto da Justificativa de Indeferimento")

    class Meta:
        verbose_name = "Justificativa de Indeferimento"
        verbose_name_plural = "Justificativas de Indeferimento"

    def __str__(self):
        return self.texto


class SituacaoAvaliacao(BaseChoice):
    DEFERIDA = "Deferida"
    INDEFERIDA = "Indeferida"


class Concluida(BaseChoice):
    NAO = "Não"
    SIM = "Sim"


@reversion.register()
class AvaliacaoAvaliador(ModelDate):
    inscricao = models.ForeignKey(
        InscricaoPreAnalise,
        verbose_name="Inscrição",
        on_delete=models.PROTECT,
        related_name="avaliacoes_avaliador",
    )
    situacao = models.CharField(
        verbose_name="Situação",
        choices=SituacaoAvaliacao.choices(blank=True),
        max_length=25,
    )
    texto_indeferimento = models.ForeignKey(
        JustificativaIndeferimento,
        null=True,
        blank=True,
        verbose_name="Justificativa do indeferimento",
        on_delete=models.PROTECT,
    )
    avaliador = models.ForeignKey(
        User,
        verbose_name="Avaliador",
        on_delete=models.PROTECT,
        related_name="avaliacoes_avaliador_psct",
    )
    concluida = models.CharField(
        verbose_name="Enviar avaliação",
        choices=Concluida.choices(blank=True),
        max_length=5,
        help_text="A avaliação não poderá mais ser editada e será entregue"
        " ao homologador após o envio.",
    )

    class Meta:
        verbose_name = "Avaliação de Avaliador"
        verbose_name_plural = "Avaliações de Avaliadores"

    @property
    def is_concluida(self):
        return self.concluida == Concluida.SIM.name

    def is_owner(self, user):
        return self.avaliador == user

    def pode_alterar(self, user):
        return (
            self.is_owner(user)
            and self.inscricao.fase.acontecendo
            and not self.is_concluida
        )

    def __str__(self):
        return f"Avaliação (avaliador) de {self.avaliador} da {self.inscricao}"

    def save(self, *args, **kwargs):

        if not self.id and self.situacao == SituacaoAvaliacao.DEFERIDA.name:
            ProgressoAnalise.objects.filter(
                fase=self.inscricao.fase,
                curso=self.inscricao.curso,
                modalidade=self.inscricao.modalidade,
            ).update(em_analise=models.F("avaliadas") + 1)

        super().save(*args, **kwargs)

        avaliacoes = self.inscricao.avaliacoes_avaliador.filter(
            concluida=Concluida.SIM.name
        )
        qnt_avaliacoes = avaliacoes.count()
        avaliadores_necessarios = self.inscricao.fase.quantidade_avaliadores

        if qnt_avaliacoes == avaliadores_necessarios:
            deferimentos = avaliacoes.filter(
                situacao=SituacaoAvaliacao.DEFERIDA.name
            ).count()
            justificativas = len(
                list(
                    avaliacoes.values_list("texto_indeferimento", flat=True).distinct()
                )
            )
            if deferimentos == 0 and justificativas == 1:
                self.inscricao.situacao = SituacaoInscricao.INDEFERIDA.name
                self.inscricao.save()
            elif deferimentos == avaliadores_necessarios:
                self.inscricao.situacao = SituacaoInscricao.DEFERIDA.name
                self.inscricao.save()
            else:
                self.inscricao.situacao = SituacaoInscricao.AGUARDANDO_HOMOLOGADOR.name
                self.inscricao.save()


@reversion.register()
class AvaliacaoHomologador(ModelDate):
    inscricao = models.ForeignKey(
        InscricaoPreAnalise,
        verbose_name="Inscrição",
        on_delete=models.PROTECT,
        related_name="avaliacoes_homologador",
    )
    situacao = models.CharField(
        verbose_name="Situação",
        choices=SituacaoAvaliacao.choices(blank=True),
        max_length=25,
    )
    texto_indeferimento = models.ForeignKey(
        JustificativaIndeferimento,
        null=True,
        blank=True,
        verbose_name="Justificativa do indeferimento",
        on_delete=models.PROTECT,
    )
    homologador = models.ForeignKey(
        User,
        verbose_name="Homologador",
        on_delete=models.PROTECT,
        related_name="avaliacoes_homologador_psct",
    )

    class Meta:
        verbose_name = "Avaliação de Homologador"
        verbose_name_plural = "Avaliações de Homologadores"

    def __str__(self):
        return f"Avaliação (homologador) de {self.homologador} da {self.inscricao}"

    def is_owner(self, user):
        return self.homologador == user

    def pode_alterar(self, user):
        return self.is_owner(user) and self.inscricao.fase.acontecendo

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.situacao == SituacaoAvaliacao.DEFERIDA.name:
            self.inscricao.situacao = SituacaoInscricao.DEFERIDA.name
            self.inscricao.save()
        if self.situacao == SituacaoAvaliacao.INDEFERIDA.name:
            self.inscricao.situacao = SituacaoInscricao.INDEFERIDA.name
            self.inscricao.save()


class RegraExclusaoGrupo(models.Model):
    fase = models.ForeignKey(
        FaseAnalise, verbose_name="Fase de análise", on_delete=models.CASCADE
    )
    coluna = models.ForeignKey(Coluna, verbose_name="Coluna", on_delete=models.PROTECT)
    valor = models.CharField(max_length=255, verbose_name="Valor de comparação")
    grupo = models.ForeignKey(Group, verbose_name="Grupo", on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Regra de Exclusão de Inscrição"
        verbose_name_plural = "Regras de Exclusão de Inscrições"

    def __str__(self):
        return f"{self.regra} do grupo {self.grupo} da {self.fase}"


class ProgressoAnaliseManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        quantidade_avaliadores = Cast(
            "fase__quantidade_avaliadores", output_field=IntegerField()
        )
        return (
            qs.annotate(
                total_inscricoes=models.Sum(
                    models.Case(
                        models.When(
                            curso__inscricoes_preanalise__modalidade=models.F(
                                "modalidade"
                            ),
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                concluida=models.Case(
                    models.When(avaliadas=models.F("meta"), then=True),
                    default=False,
                    output_field=models.BooleanField(),
                ),
                restantes=models.F("meta")
                - (models.F("avaliadas") / quantidade_avaliadores),
                meta_atingida=((models.F("avaliadas") / quantidade_avaliadores) * 100)
                / models.F("meta"),
                porcentagem_analise=(
                    (models.F("em_analise") / quantidade_avaliadores) * 100
                )
                / models.F("meta"),
            )
            .annotate(
                inscricoes_pendentes=models.Case(
                    models.When(
                        total_inscricoes=(
                            models.F("avaliadas") / quantidade_avaliadores
                        ),
                        then=False,
                    ),
                    default=True,
                    output_field=models.BooleanField(),
                )
            )
            .order_by("meta_atingida", "porcentagem_analise")
        )


class ProgressoAnalise(models.Model):
    fase = models.ForeignKey(
        FaseAnalise, verbose_name="Fase de Análise", on_delete=models.CASCADE
    )
    curso = models.ForeignKey(
        CursoSelecao, verbose_name="Curso", on_delete=models.CASCADE
    )
    modalidade = models.ForeignKey(
        Modalidade, verbose_name="Modalidade", on_delete=models.CASCADE
    )
    avaliadas = models.IntegerField(
        verbose_name="Quantidade de Inscrições Avaliadas", default=0
    )
    em_analise = models.IntegerField(
        verbose_name="Quantidade de Inscrições em Análise", default=0
    )
    meta = models.IntegerField(verbose_name="Meta")

    objects = models.Manager()
    ordered_objects = ProgressoAnaliseManager()

    class Meta:
        verbose_name = "Progresso da Análise"
        verbose_name_plural = "Progressos das Análises"

    @classmethod
    def get_proximas_avaliador(cls, fase, avaliador):
        return (
            cls.ordered_objects.annotate(
                minhas_inscricoes_incompletas=models.Case(
                    models.When(
                        curso__inscricoes_preanalise__avaliacoes_avaliador__avaliador=avaliador,
                        curso__inscricoes_preanalise__avaliacoes_homologador__isnull=True,
                        curso__inscricoes_preanalise__modalidade=models.F("modalidade"),
                        then=1,
                    ),
                    default=0,
                    output_field=models.IntegerField(),
                )
            )
            .filter(fase=fase, inscricoes_pendentes=True)
            .order_by(
                "meta_atingida", "porcentagem_analise", "minhas_inscricoes_incompletas"
            )
            .distinct()
        )

    @classmethod
    def existe_avaliacao_pendente(cls, fase):
        return cls.ordered_objects.filter(fase=fase, inscricoes_pendentes=True).exists()


def get_lote_avaliador(fase, avaliador, quantidade):

    with transaction.atomic():

        excludes = RegraExclusaoGrupo.objects.filter(
            grupo__user=avaliador, fase=fase
        ).values_list("coluna__query_string", "valor")

        if excludes.exists():
            sub_qs = reduce(
                operator.or_, [models.Q(**{path: valor}) for (path, valor) in excludes]
            )
        else:
            sub_qs = None

        quantidade_lote = 0
        mailbox, created = MailBoxAvaliadorInscricao.objects.get_or_create(
            fase=fase, avaliador=avaliador
        )

        qs = (
            InscricaoPreAnalise.objects.exclude(
                mailbox_avaliadores__avaliador=avaliador
            )
            .annotate(avaliadores=models.Count("mailbox_avaliadores"))
            .filter(
                situacao=SituacaoInscricao.AVALIADOR_FALTANDO.name,
                fase=fase,
                avaliadores__lt=models.F("fase__quantidade_avaliadores"),
            )
            .distinct()
        )

        if sub_qs:
            qs = qs.exclude(sub_qs)

        inscricoes = qs[:quantidade]
        total_inscricoes = inscricoes.count()

        if total_inscricoes:
            quantidade_lote += total_inscricoes

            for inscricao in inscricoes:
                if inscricao.avaliadores == 0:
                    inscricao.situacao = SituacaoInscricao.AVALIADOR_FALTANDO.name
                    inscricao.save()
                if inscricao.avaliadores == 1:
                    inscricao.situacao = SituacaoInscricao.AVALIACAO_PENDENTE.name
                    inscricao.save()
                mailbox.add(inscricao)

            if quantidade_lote == quantidade:
                return quantidade_lote

        # pega o resto das inscrições pendentes FIX TODO
        # rodrigo.araujo@ifpb.edu.br 01/12/2016

        qs = (
            InscricaoPreAnalise.objects.exclude(
                mailbox_avaliadores__avaliador=avaliador
            )
            .annotate(avaliadores=models.Count("mailbox_avaliadores"))
            .filter(
                situacao=SituacaoInscricao.SEM_AVALIADORES.name,
                fase=fase,
                avaliadores=0,
            )
            .distinct()
        )

        if sub_qs:
            qs = qs.exclude(sub_qs)

        inscricoes = qs[: quantidade - quantidade_lote]
        total_inscricoes = inscricoes.count()

        if total_inscricoes:
            quantidade_lote += total_inscricoes

            for inscricao in inscricoes:
                if inscricao.avaliadores == 0:
                    inscricao.situacao = SituacaoInscricao.AVALIADOR_FALTANDO.name
                    inscricao.save()
                if inscricao.avaliadores == 1:
                    inscricao.situacao = SituacaoInscricao.AVALIACAO_PENDENTE.name
                    inscricao.save()
                mailbox.add(inscricao)

            if quantidade_lote == quantidade:
                return quantidade_lote

        # -------------------------------------------------------------

        proximas = ProgressoAnalise.get_proximas_avaliador(fase, avaliador)
        for proxima in proximas:
            qs = (
                InscricaoPreAnalise.objects.exclude(
                    mailbox_avaliadores__avaliador=avaliador
                )
                .annotate(avaliadores=models.Count("mailbox_avaliadores"))
                .filter(
                    curso=proxima.curso,
                    fase=fase,
                    modalidade=proxima.modalidade,
                    situacao=SituacaoInscricao.SEM_AVALIADORES.name,
                    avaliadores=0,
                )
                .distinct()
            )

            if sub_qs:
                qs = qs.exclude(sub_qs)

            inscricoes = qs[: quantidade - quantidade_lote]
            proxima.em_analise += 1
            proxima.save()

            for inscricao in inscricoes:
                if inscricao.avaliadores == 0:
                    inscricao.situacao = SituacaoInscricao.AVALIADOR_FALTANDO.name
                    inscricao.save()
                if inscricao.avaliadores == 1:
                    inscricao.situacao = SituacaoInscricao.AVALIACAO_PENDENTE.name
                    inscricao.save()
                mailbox.add(inscricao)

            quantidade_lote += inscricoes.count()

            if quantidade_lote >= quantidade:
                break

    return quantidade_lote


def get_lote_homologador(fase, homologador, quantidade):
    quantidade_lote = 0

    with transaction.atomic():

        mailbox, created = MailBoxHomologadorInscricao.objects.get_or_create(
            fase=fase, homologador=homologador
        )
        qs = (
            InscricaoPreAnalise.objects.filter(
                fase=fase,
                situacao=SituacaoInscricao.AGUARDANDO_HOMOLOGADOR.name,
                mailbox_homologadores__isnull=True,
            )
            .exclude(avaliacoes_avaliador__avaliador=homologador)
            .distinct()
        )

        excludes = RegraExclusaoGrupo.objects.filter(
            grupo__user=homologador, fase=fase
        ).values_list("coluna__query_string", "valor")

        if excludes.exists():
            sub_qs = reduce(
                operator.or_, [models.Q(**{path: valor}) for (path, valor) in excludes]
            )
            qs = qs.exclude(sub_qs)

        inscricoes = qs[: quantidade - quantidade_lote]
        quantidade_lote += inscricoes.count()
        mailbox.inscricoes.add(*inscricoes)

    return quantidade_lote


@receiver(post_save, sender=ModalidadeVagaCursoEdital)
def create_progresso_analise(sender, instance, *args, **kwargs):
    fases = instance.curso_edital.edital.faseanalise_set.all()
    for fase in fases:
        if fase.acontecendo and instance.quantidade_vagas:
            meta = instance.quantidade_vagas * instance.multiplicador
            ProgressoAnalise.objects.update_or_create(
                defaults=dict(meta=meta),
                fase=fase,
                curso=instance.curso_edital.curso,
                modalidade=instance.modalidade,
            )
