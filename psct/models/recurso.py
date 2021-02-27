from datetime import datetime

import reversion
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from suaprest.django import get_or_create_user

from base.utils import exists
from editais.models import Edital
from psct.models.inscricao import Inscricao


class ModelDate(models.Model):
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data do Cadastro"
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True, verbose_name="Data da Atualização"
    )

    class Meta:
        abstract = True


@reversion.register()
class FaseRecurso(ModelDate):
    nome = models.CharField(verbose_name="Nome da Fase", max_length=255)
    edital = models.ForeignKey(Edital, verbose_name="Edital", on_delete=models.PROTECT)
    data_inicio_submissao = models.DateTimeField(
        verbose_name="Início da Submissão de Recursos"
    )
    data_encerramento_submissao = models.DateTimeField(
        verbose_name="Encerramento da Submissão de Recursos"
    )
    data_inicio_analise = models.DateTimeField(
        verbose_name="Início da Análise de Recursos"
    )
    data_encerramento_analise = models.DateTimeField(
        verbose_name="Encerramento da Análise de Recursos"
    )
    data_resultado = models.DateTimeField(
        verbose_name="Data de divulgação do resultado dos recursos"
    )
    quantidade_avaliadores = models.PositiveSmallIntegerField(
        verbose_name="Quantidade de Avaliadores", default=1
    )
    requer_homologador = models.BooleanField(
        verbose_name="Requer homologador?", default=True
    )
    avaliadores = models.ForeignKey(
        "psct.GrupoEdital",
        verbose_name="Grupo de Avaliadores",
        related_name="fase_recurso_avaliadores",
        on_delete=models.PROTECT,
    )
    homologadores = models.ForeignKey(
        "psct.GrupoEdital",
        verbose_name="Grupo de Homologadores",
        related_name="fase_recurso_homologadores",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "Fase de Recurso"
        verbose_name_plural = "Fases de Recursos"

    def __str__(self):
        return f"{self.nome} - Edital {self.edital.numero}/{self.edital.ano}"

    @property
    def em_periodo_submissao(self):
        return (
            self.data_inicio_submissao
            <= datetime.now()
            <= self.data_encerramento_submissao
        )

    @property
    def em_periodo_analise(self):
        return (
            self.data_inicio_analise <= datetime.now() <= self.data_encerramento_analise
        )

    @property
    def pode_redistribuir(self):
        return self.em_periodo_analise

    @property
    def pode_distribuir(self):
        return (
            self.data_encerramento_submissao < datetime.now() < self.data_inicio_analise
        )

    def clean(self):
        if (
            exists(self.data_encerramento_submissao, self.data_inicio_submissao)
            and self.data_encerramento_submissao < self.data_inicio_submissao
        ):
            raise ValidationError(
                {
                    "data_encerramento_submissao": "A data de encerramento do período de submissão não pode ser anterior ao seu início"
                }
            )
        if (
            exists(self.data_inicio_analise, self.data_inicio_analise)
            and self.data_encerramento_analise < self.data_inicio_analise
        ):
            raise ValidationError(
                {
                    "data_encerramento_analise": "A data de encerramento do período de análise não pode ser anterior ao seu início"
                }
            )
        if (
            exists(self.data_resultado, self.data_encerramento_analise)
            and self.data_resultado <= self.data_encerramento_analise
        ):
            raise ValidationError(
                {
                    "data_resultado": "A data de divulgação do resultado não pode ser anterior ao encerramento do período de análise"
                }
            )
        if (
            exists(self.data_inicio_analise, self.data_encerramento_submissao)
            and self.data_inicio_analise <= self.data_encerramento_submissao
        ):
            raise ValidationError(
                {
                    "data_inicio_analise": "A data de início da análise dos recursos não pode ser anterior ao encerramento da submissão"
                }
            )
        if (
            exists(self.data_inicio_submissao, self.edital_id)
            and self.data_inicio_submissao.date()
            <= self.edital.processo_inscricao.data_encerramento
        ):
            raise ValidationError(
                {
                    "data_inicio_submissao": "A fase de recurso só pode começar após o encerramento das inscrições"
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


@reversion.register()
class Recurso(ModelDate):
    fase = models.ForeignKey(
        FaseRecurso, verbose_name="Fase de Recurso", on_delete=models.PROTECT
    )
    usuario = models.ForeignKey(User, verbose_name="Usuário", on_delete=models.PROTECT)
    inscricao = models.ForeignKey(
        Inscricao, verbose_name="Inscrição", on_delete=models.PROTECT
    )
    texto = models.TextField(verbose_name="Texto do recurso")

    class Meta:
        verbose_name = "Recurso"
        verbose_name_plural = "Recursos"

    def __str__(self):
        return f"Recurso de {self.inscricao}"

    def get_grupo_avaliadores(self):
        return self.mailbox_grupo_avaliadores.first()

    def get_grupo_homologadores(self):
        return self.mailbox_grupo_homologadores.first()

    def get_avaliadores(self):
        return [m.avaliador for m in self.mailbox_avaliadores.all()]

    def get_homologador(self):
        mailbox = self.mailbox_homologadores.first()
        if mailbox:
            return mailbox.homologador

    @property
    def pode_ver_parecer(self):
        return datetime.now() >= self.fase.data_resultado

    @property
    def homologador_pode_emitir_parecer(self):
        avaliacoes = self.pareceres_avaliadores.count()
        return avaliacoes == self.fase.quantidade_avaliadores

    @property
    def parecer(self):
        return self.pareceres_homologadores.first()


class GrupoEdital(models.Model):
    grupo = models.ForeignKey(
        Group,
        related_name="grupos_editais",
        verbose_name="Grupo",
        on_delete=models.PROTECT,
    )
    edital = models.ForeignKey(Edital, verbose_name="Edital", on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Grupo de Edital"
        verbose_name_plural = "Grupos de Edtais"
        ordering = ("grupo__name",)

    def __str__(self):
        return f"{self.grupo.name} - {self.edital}"


class MailBoxGrupoAvaliadores(models.Model):
    fase = models.ForeignKey(
        FaseRecurso,
        verbose_name="Fase do Recurso",
        on_delete=models.PROTECT,
        related_name="mailbox_grupo_avaliadores",
    )
    grupo = models.ForeignKey(
        Group,
        verbose_name="Grupo",
        on_delete=models.PROTECT,
        related_name="mailbox_grupo_avaliadores",
    )
    recursos = models.ManyToManyField(
        Recurso, verbose_name="recursos", related_name="mailbox_grupo_avaliadores"
    )

    class Meta:
        verbose_name = "Recursos do Grupo de Avaliadores"
        verbose_name_plural = "Recursos dos Grupos de Avaliadores"

    def __str__(self):
        return f"Recursos de Avaliadores do Grupo: {self.grupo}"


class MailBoxGrupoHomologadores(models.Model):
    fase = models.ForeignKey(
        FaseRecurso,
        verbose_name="Fase do Recurso",
        on_delete=models.PROTECT,
        related_name="mailbox_grupo_homologadores",
    )
    grupo = models.ForeignKey(
        Group,
        verbose_name="Grupo",
        on_delete=models.PROTECT,
        related_name="mailbox_grupo_homologadores",
    )
    recursos = models.ManyToManyField(
        Recurso, verbose_name="recursos", related_name="mailbox_grupo_homologadores"
    )

    class Meta:
        verbose_name = "Recursos do Grupo de Homologadores"
        verbose_name_plural = "Recursos dos Grupos de Homologadores"

    def __str__(self):
        return f"Recursos de Homologadores do Grupo: {self.grupo}"


class MailBoxAvaliador(models.Model):
    fase = models.ForeignKey(
        FaseRecurso,
        verbose_name="Fase do Recurso",
        on_delete=models.PROTECT,
        related_name="mailbox_avaliadores",
    )
    recursos = models.ManyToManyField(
        Recurso, verbose_name="recursos", related_name="mailbox_avaliadores"
    )
    avaliador = models.ForeignKey(
        User,
        verbose_name="Avaliador",
        on_delete=models.PROTECT,
        related_name="mailbox_avaliador",
    )

    class Meta:
        verbose_name = "Caixa de Recursos do Avaliador"
        verbose_name_plural = "Caixas de Recursos dos Avaliadores"
        unique_together = ("fase", "avaliador")

    def __str__(self):
        return f"Caixa de Recursos do Avaliador {self.avaliador}"


class MailBoxHomologador(models.Model):
    fase = models.ForeignKey(
        FaseRecurso,
        verbose_name="Fase do Recurso",
        on_delete=models.PROTECT,
        related_name="mailbox_homologadores",
    )
    recursos = models.ManyToManyField(
        Recurso, verbose_name="recursos", related_name="mailbox_homologadores"
    )
    homologador = models.ForeignKey(
        User,
        verbose_name="Homologador",
        on_delete=models.PROTECT,
        related_name="mailbox_homologador",
    )

    class Meta:
        verbose_name = "Caixa de Recursos do Homologador"
        verbose_name_plural = "Caixas de Recursos dos Homologadores"
        unique_together = ("fase", "homologador")

    def __str__(self):
        return f"Caixa de Recursos do Homologador {self.homologador}"


SITUACAO_CHOICES = [("", "------"), (False, "Indeferida"), (True, "Deferida")]

CONCLUIDO_CHOICES = [("", "------"), (False, "Não"), (True, "Sim")]


@reversion.register()
class ParecerAvaliador(ModelDate):
    recurso = models.ForeignKey(
        Recurso,
        verbose_name="Recurso",
        on_delete=models.PROTECT,
        related_name="pareceres_avaliadores",
    )
    texto = models.TextField(verbose_name="Texto do Parecer")
    aceito = models.BooleanField(verbose_name="Situação", choices=SITUACAO_CHOICES)
    avaliador = models.ForeignKey(
        User,
        verbose_name="Avaliador",
        on_delete=models.PROTECT,
        related_name="pareceres_avaliador",
    )
    concluido = models.BooleanField(
        verbose_name="Enviar avaliação",
        choices=CONCLUIDO_CHOICES,
        help_text="O parecer não poderá mais ser editado e será entregue"
        " ao homologador.",
    )

    class Meta:
        verbose_name = "Parecer Avaliador"
        verbose_name_plural = "Pareceres de Avaliadores"

    def __str__(self):
        return "Parecer emitido por {} referente ao recurso {}".format(
            self.avaliador, self.recurso
        )


@reversion.register()
class ParecerHomologador(ModelDate):
    recurso = models.ForeignKey(
        Recurso,
        verbose_name="Recurso",
        on_delete=models.PROTECT,
        related_name="pareceres_homologadores",
    )
    texto = models.TextField(verbose_name="Texto do Parecer")
    aceito = models.BooleanField(verbose_name="Situação", choices=SITUACAO_CHOICES)
    homologador = models.ForeignKey(
        User,
        verbose_name="Homologador",
        on_delete=models.PROTECT,
        related_name="pareceres_homologador",
    )

    class Meta:
        verbose_name = "Parecer Homologador"
        verbose_name_plural = "Pareceres de Homologadores"

    def __str__(self):
        return "Parecer emitido por {} referente ao recurso {}".format(
            self.homologador, self.recurso
        )

    @property
    def status(self):
        if self.aceito:
            return "Deferido"
        return "Indeferido"


@transaction.atomic
def create_grupo_recurso(edital, nome, servidores, merge, exclude):
    grupo = Group.objects.create(name=nome)
    users = [get_or_create_user(matricula, is_staff=False) for matricula in servidores]
    grupo.user_set.add(*users)
    update_grupo(grupo, merge, exclude)
    return GrupoEdital.objects.create(grupo=grupo, edital=edital)


@transaction.atomic
def update_grupo_recurso(grupo, nome, servidores, merge, exclude):
    grupo.name = nome
    users = [get_or_create_user(matricula, is_staff=False) for matricula in servidores]
    grupo.save()
    grupo.user_set.clear()
    grupo.user_set.add(*users)
    update_grupo(grupo, merge, exclude)


def update_grupo(grupo, merge, exclude):
    merge = GrupoEdital.objects.filter(id__in=merge)
    exclude = GrupoEdital.objects.filter(id__in=exclude)

    for grupo_edital in merge:
        grupo.user_set.add(*grupo_edital.grupo.user_set.all())
    for grupo_edital in exclude:
        users = grupo_edital.grupo.user_set.filter(
            id__in=grupo.user_set.values_list("id", flat=True)
        )
        grupo.user_set.remove(*users)
