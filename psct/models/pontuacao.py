import operator
from datetime import datetime
from functools import reduce

import reversion
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.db.models import Q

from base.utils import exists
from psct.models import analise as analise_models
from psct.models import inscricao as inscricao_models
from psct.models import recurso as recurso_models


@reversion.register()
class FaseAjustePontuacao(recurso_models.ModelDate):
    fase_analise = models.OneToOneField(
        analise_models.FaseAnalise,
        related_name="ajuste_pontuacao",
        verbose_name="Fase de Analise",
        on_delete=models.PROTECT,
    )
    data_inicio = models.DateTimeField(verbose_name="Data de Início")
    data_encerramento = models.DateTimeField(verbose_name="Data de encerramento")
    avaliadores = models.ForeignKey(
        recurso_models.GrupoEdital,
        verbose_name="Grupo de Avaliadores",
        related_name="fase_pontuacao_avaliadores",
        on_delete=models.PROTECT,
    )
    homologadores = models.ForeignKey(
        recurso_models.GrupoEdital,
        verbose_name="Grupo de Homologadores",
        related_name="fase_pontuacao_homologadores",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "Fase de Ajuste de Pontuação"
        verbose_name_plural = "Fases de Ajuste de Pontuação"

    def __str__(self):
        return "Fase de Ajuste - Edital {}/{}".format(
            self.fase_analise.edital.numero, self.fase_analise.edital.ano
        )

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
            exists(self.avaliadores_id, self.fase_analise_id)
            and self.avaliadores.edital != self.fase_analise.edital
        ):
            raise ValidationError(
                {
                    "avaliadores": "O grupo de avaliadores não pertence ao edital selecionado"
                }
            )

        if (
            exists(self.homologadores_id, self.fase_analise_id)
            and self.homologadores.edital != self.fase_analise.edital
        ):
            raise ValidationError(
                {
                    "homologadores": "O grupo de homologadores não pertence ao edital selecionado"
                }
            )

        if exists(self.avaliadores_id, self.homologadores_id):
            h_users = set(self.homologadores.grupo.user_set.all())
            users = set(self.avaliadores.grupo.user_set.all())
            if users & h_users:
                raise ValidationError(
                    "Existem membros do grupo de homologadores presentes no grupo de avaliação"
                )

            if len(users) < len(h_users):
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

        homologadores = Group.objects.get(name="Homologador PSCT")
        homologadores.user_set.add(*self.homologadores.grupo.user_set.all())

    def existe_inscricao_pendente_ajuste(self):
        try:
            return self.pilha.inscricoes.filter(
                pontuacoes_avaliadores__isnull=True
            ).exists()
        except PilhaInscricaoAjuste.DoesNotExist:
            return False

    def existe_inscricao_pendente_homologacao(self):
        try:
            return self.pilha.inscricoes.filter(
                pontuacoes_homologadores__isnull=True,
                pontuacoes_avaliadores__concluida=analise_models.Concluida.SIM.name,
            ).exists()
        except PilhaInscricaoAjuste.DoesNotExist:
            return False


@reversion.register()
class PontuacaoAvaliador(recurso_models.ModelDate, inscricao_models.PontuacaoBase):
    fase = models.ForeignKey(
        FaseAjustePontuacao,
        verbose_name="Fase de Ajuste de Pontuação",
        related_name="pontuacoes_avaliadores",
        on_delete=models.PROTECT,
    )
    inscricao = models.ForeignKey(
        inscricao_models.Inscricao,
        verbose_name="Inscrição",
        related_name="pontuacoes_avaliadores",
        on_delete=models.PROTECT,
    )
    inscricao_preanalise = models.ForeignKey(
        analise_models.InscricaoPreAnalise,
        verbose_name="Inscrição Pré-Análise",
        related_name="pontuacoes_avaliadores",
        on_delete=models.PROTECT,
    )
    avaliador = models.ForeignKey(
        analise_models.User,
        verbose_name="Avaliador",
        related_name="pontuacoes_avaliadores",
        on_delete=models.PROTECT,
    )
    valor = models.DecimalField(
        verbose_name="Valor",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )
    valor_pt = models.DecimalField(
        verbose_name="Valor de desempate PT",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )
    valor_mt = models.DecimalField(
        verbose_name="Valor de desempate MT",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )
    ensino_regular = models.BooleanField(
        verbose_name="Candidato cursou o ensino regular?", default=True
    )
    concluida = models.CharField(
        verbose_name="Enviar avaliação",
        choices=analise_models.Concluida.choices(blank=True),
        max_length=5,
        help_text="A pontuação não poderá mais ser editada e será entregue"
        " ao homologador após o envio.",
    )

    class Meta:
        verbose_name = "Pontuação Avaliador"
        verbose_name_plural = "Pontuações de Avaliadores"

    def __str__(self):
        return f"Pontuação Avaliador {self.inscricao}"

    @property
    def is_concluida(self):
        return self.concluida == analise_models.Concluida.SIM.name

    def is_owner(self, user):
        return self.avaliador == user

    def pode_alterar(self, user):
        return self.is_owner(user) and self.fase.acontecendo and not self.is_concluida

    def pode_ver(self, user):
        return self.is_owner(user) and self.is_concluida

    @property
    def user(self):
        return self.avaliador

    @property
    def user_profile_name(self):
        return "Avaliador"


@reversion.register()
class NotaAnualAvaliador(recurso_models.ModelDate):
    ANO_CHOICES = [
        (0, "Supletivo/Enem/Outros"),  # Supletivo ou ENEM
        (6, 6),
        (7, 7),
        (8, 8),
        (1, 1),
        (2, 2),
    ]
    pontuacao = models.ForeignKey(
        PontuacaoAvaliador,
        verbose_name="Pontuação da Inscrição",
        related_name="notas",
        on_delete=models.PROTECT,
    )
    ano = models.PositiveSmallIntegerField(verbose_name="Ano", choices=ANO_CHOICES)
    portugues = models.DecimalField(
        verbose_name="Português",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )
    matematica = models.DecimalField(
        verbose_name="Matemática",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )
    historia = models.DecimalField(
        verbose_name="História",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )
    geografia = models.DecimalField(
        verbose_name="Geografia",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )

    class Meta:
        verbose_name = "Nota Anual Avaliador"
        verbose_name_plural = "Notas Anuais de Avaliadores"
        ordering = ("ano",)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.pontuacao.update_pontuacao()

    def __str__(self):
        if self.ano:
            return f"Notas do {self.ano} ano"
        return "Notas"


@reversion.register()
class PontuacaoHomologador(recurso_models.ModelDate, inscricao_models.PontuacaoBase):
    fase = models.ForeignKey(
        FaseAjustePontuacao,
        verbose_name="Fase de Ajuste de Pontuação",
        related_name="pontuacoes_homologadores",
        on_delete=models.PROTECT,
    )
    inscricao = models.ForeignKey(
        inscricao_models.Inscricao,
        verbose_name="Inscrição",
        related_name="pontuacoes_homologadores",
        on_delete=models.PROTECT,
    )
    inscricao_preanalise = models.ForeignKey(
        analise_models.InscricaoPreAnalise,
        verbose_name="Inscrição Pré-Análise",
        related_name="pontuacoes_homologadores",
        on_delete=models.PROTECT,
    )
    homologador = models.ForeignKey(
        analise_models.User,
        verbose_name="Homologador",
        related_name="pontuacoes_homologadores",
        on_delete=models.PROTECT,
    )
    valor = models.DecimalField(
        verbose_name="Valor",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )
    valor_pt = models.DecimalField(
        verbose_name="Valor de desempate PT",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )
    valor_mt = models.DecimalField(
        verbose_name="Valor de desempate MT",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )
    ensino_regular = models.BooleanField(
        verbose_name="Candidato cursou o ensino regular?", default=True
    )

    class Meta:
        verbose_name = "Pontuação Homologador"
        verbose_name_plural = "Pontuações de Homologadores"

    def __str__(self):
        return f"Pontuação Homologador {self.inscricao}"

    def is_owner(self, user):
        return self.homologador == user

    def pode_alterar(self, user):
        return self.is_owner(user) and self.fase.acontecendo

    def pode_ver(self, user):
        return self.is_owner(user)

    @property
    def user(self):
        return self.homologador

    @property
    def user_profile_name(self):
        return "Homologador"

    def deferir(self):
        self.inscricao_preanalise.situacao = (
            analise_models.SituacaoInscricao.DEFERIDA.name
        )
        self.inscricao_preanalise.pontuacao = self.valor
        self.inscricao_preanalise.pontuacao_pt = self.valor_pt
        self.inscricao_preanalise.pontuacao_mt = self.valor_mt
        self.inscricao_preanalise.save()

    def indeferir(self):
        self.inscricao_preanalise.situacao = (
            analise_models.SituacaoInscricao.INDEFERIDA.name
        )
        self.inscricao_preanalise.pontuacao = self.inscricao.pontuacao.valor
        self.inscricao_preanalise.pontuacao_pt = self.inscricao.pontuacao.valor_pt
        self.inscricao_preanalise.pontuacao_mt = self.inscricao.pontuacao.valor_mt
        self.inscricao_preanalise.save()


@reversion.register()
class NotaAnualHomologador(recurso_models.ModelDate):
    ANO_CHOICES = [
        (0, "Supletivo/Enem/Outros"),  # Supletivo ou ENEM
        (6, 6),
        (7, 7),
        (8, 8),
        (1, 1),
        (2, 2),
    ]
    pontuacao = models.ForeignKey(
        PontuacaoHomologador,
        verbose_name="Pontuação da Inscrição",
        related_name="notas",
        on_delete=models.PROTECT,
    )
    ano = models.PositiveSmallIntegerField(verbose_name="Ano", choices=ANO_CHOICES)
    portugues = models.DecimalField(
        verbose_name="Português",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )
    matematica = models.DecimalField(
        verbose_name="Matemática",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )
    historia = models.DecimalField(
        verbose_name="História",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )
    geografia = models.DecimalField(
        verbose_name="Geografia",
        max_digits=5,
        decimal_places=2,
        default=inscricao_models.ZERO,
    )

    class Meta:
        verbose_name = "Nota Anual Homologador"
        verbose_name_plural = "Notas Anuais de Homologadores"
        ordering = ("ano",)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.pontuacao.update_pontuacao()

    def __str__(self):
        if self.ano:
            return f"Notas do {self.ano} ano"
        return "Notas"


class PilhaInscricaoAjuste(recurso_models.ModelDate):
    fase = models.OneToOneField(
        FaseAjustePontuacao,
        verbose_name="Fase de Ajuste",
        on_delete=models.PROTECT,
        related_name="pilha",
    )
    inscricoes = models.ManyToManyField(
        analise_models.InscricaoPreAnalise, verbose_name="Inscrições"
    )

    class Meta:
        verbose_name = "Pilha de Inscrição para Ajuste"
        verbose_name_plural = "Pilhas de Inscrições para ajuste"


class MailboxPontuacaoAvaliador(recurso_models.ModelDate):
    fase = models.ForeignKey(
        FaseAjustePontuacao,
        verbose_name="Fase de Ajuste de Pontuação",
        on_delete=models.PROTECT,
        related_name="mailbox_pontuacao_avaliador",
    )
    avaliador = models.ForeignKey(
        analise_models.User,
        verbose_name="Avaliador",
        on_delete=models.PROTECT,
        related_name="mailbox_pontuacao_avaliador",
    )
    inscricoes = models.ManyToManyField(
        analise_models.InscricaoPreAnalise,
        verbose_name="Inscrições",
        related_name="mailbox_pontuacao_avaliador",
    )

    class Meta:
        verbose_name = "Caixa de Pontuação do Avaliador"
        verbose_name_plural = "Caixas de Pontuação do Avaliador"

    @classmethod
    def possui_inscricao_pendente(cls, fase, avaliador):
        return cls.objects.filter(
            Q(
                inscricoes__pontuacoes_avaliadores__concluida=analise_models.Concluida.NAO.name
            )
            | Q(inscricoes__pontuacoes_avaliadores__isnull=True),
            inscricoes__isnull=False,
            fase=fase,
            avaliador=avaliador,
        ).exists()

    def pode_devolver(self, inscricao):
        possui = self.inscricoes.filter(id=inscricao.id).exists()
        outro = (
            MailboxPontuacaoAvaliador.objects.filter(inscricoes=inscricao)
            .exclude(avaliador=self.avaliador)
            .exists()
        )
        avaliou = PontuacaoAvaliador.objects.filter(
            avaliador=self.avaliador, inscricao_preanalise=inscricao
        ).exists()
        return possui and outro and not avaliou


class MailboxPontuacaoHomologador(recurso_models.ModelDate):
    fase = models.ForeignKey(
        FaseAjustePontuacao,
        verbose_name="Fase de Ajuste de Pontuação",
        on_delete=models.PROTECT,
        related_name="mailbox_pontuacao_homologador",
    )
    homologador = models.ForeignKey(
        analise_models.User,
        verbose_name="Homologador",
        on_delete=models.PROTECT,
        related_name="mailbox_pontuacao_homologador",
    )
    inscricoes = models.ManyToManyField(
        analise_models.InscricaoPreAnalise,
        verbose_name="Inscrições",
        related_name="mailbox_pontuacao_homologador",
    )

    class Meta:
        verbose_name = "Caixa de Pontuação do Homologador"
        verbose_name_plural = "Caixas de Pontuação do Homologador"

    @classmethod
    def possui_inscricao_pendente(cls, fase, homologador):
        return cls.objects.filter(
            inscricoes__isnull=False,
            inscricoes__pontuacoes_homologadores__isnull=True,
            fase=fase,
            homologador=homologador,
        ).exists()

    def pode_devolver(self, inscricao):
        possui = self.inscricoes.filter(id=inscricao.id).exists()
        outro = (
            MailboxPontuacaoHomologador.objects.filter(inscricoes=inscricao)
            .exclude(homologador=self.homologador)
            .exists()
        )
        avaliou = PontuacaoHomologador.objects.filter(
            homologador=self.homologador, inscricao_preanalise=inscricao
        ).exists()
        return possui and outro and not avaliou


def get_lote_avaliador(fase, avaliador, quantidade):
    quantidade_lote = 0

    with transaction.atomic():
        mailbox, created = MailboxPontuacaoAvaliador.objects.get_or_create(
            fase=fase, avaliador=avaliador
        )
        qs = fase.pilha.inscricoes.filter(mailbox_pontuacao_avaliador__isnull=True)

        excludes = analise_models.RegraExclusaoGrupo.objects.filter(
            grupo__user=avaliador, fase=fase.fase_analise
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


def get_lote_homologador(fase, homologador, quantidade):
    quantidade_lote = 0

    with transaction.atomic():
        mailbox, created = MailboxPontuacaoHomologador.objects.get_or_create(
            fase=fase, homologador=homologador
        )
        qs = fase.pilha.inscricoes.filter(
            pontuacoes_avaliadores__isnull=False,
            pontuacoes_avaliadores__concluida=analise_models.Concluida.SIM.name,
            mailbox_pontuacao_homologador__isnull=True,
        )

        excludes = analise_models.RegraExclusaoGrupo.objects.filter(
            grupo__user=homologador, fase=fase.fase_analise
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
