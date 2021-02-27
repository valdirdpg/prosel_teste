import datetime

from ckeditor_uploader.fields import RichTextUploadingField
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from editais.choices import (
    CategoriaDocumentoChoices,
    CronogramaChoices,
    EditalChoices,
    EventoCronogramaChoices,
)
from editais.validators import DOCUMENT_EXTENSIONS, FileValidator
from noticias.models import PalavrasChave
from processoseletivo.models import Edicao, Etapa


class Edital(models.Model):

    nome = models.CharField(max_length=255)
    numero = models.PositiveSmallIntegerField(verbose_name="Número")
    ano = models.PositiveIntegerField(verbose_name="Ano")
    data_publicacao = models.DateField(verbose_name="Data de Publicação")
    edicao = models.ForeignKey(
        Edicao, verbose_name="Edição de Processo Seletivo", on_delete=models.PROTECT
    )
    encerrado = models.BooleanField(verbose_name="Edital Encerrado", default=False)
    publicado = models.BooleanField(verbose_name="Edital Publicado", default=False)
    descricao = RichTextUploadingField(config_name="editais", verbose_name="Descrição")
    prazo_pagamento = models.DateField(verbose_name="Data de Pagamento")
    link_inscricoes = models.URLField(
        blank=True, null=True, verbose_name="Link para Inscrições"
    )
    setor_responsavel = models.CharField(
        max_length=255, verbose_name="Setor Responsável"
    )
    tipo = models.CharField(max_length=255, choices=EditalChoices.choices())
    retificado = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="retificacoes",
        verbose_name="Edital Retificado",
        on_delete=models.SET_NULL,
    )
    palavra_chave = models.ForeignKey(
        PalavrasChave,
        on_delete=models.CASCADE,
        help_text="Palavra-chave para relacionar com as notícias referentes a esse edital.",
        verbose_name="Palavra-chave",
    )
    url_video_descricao = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL de vídeo descritivo do edital",
        help_text='Copiar o endereço "src" que aparece na opção de compartilhamento '
        '"Incorporar" do YouTube.',
    )

    def __str__(self):
        return "{0.nome} - {0.numero}/{0.ano}".format(self)

    class Meta:
        verbose_name = "Edital"
        verbose_name_plural = "Editais"

    def get_absolute_url(self):
        return reverse(
            "edicao", args=[self.edicao.processo_seletivo.id, self.edicao.id]
        )

    def has_anexo(self):
        return self.documentos.filter(categoria="ANEXO").exists()

    def has_local_prova(self):
        return self.documentos.filter(categoria="LOCALPROVA").exists()

    def has_prova_gabarito(self):
        return (
            self.documentos.filter(categoria="PROVA").exists()
            or self.documentos.filter(categoria="GABARITO").exists()
        )

    def get_link_edital(self):
        doc = Documento.objects.filter(edital=self)
        return doc.first().link_arquivo_externo

    def has_resultado(self):
        return self.documentos.filter(categoria="RESULTADO").exists()

    def has_recurso(self):
        return self.documentos.filter(categoria="RECURSO").exists()

    def inscricoes_abertas(self):
        cronograma = self.cronogramas_selecao.filter(inscricao=True).first()
        if cronograma:
            return cronograma.is_vigente()
        return False

    def iniciou_inscricoes(self):
        cronograma = self.cronogramas_selecao.filter(inscricao=True).first()
        if cronograma:
            return cronograma.inicio <= datetime.date.today()
        return False


class NivelSelecao(models.Model):
    nome = models.CharField(max_length=255)
    vagas = models.PositiveIntegerField(verbose_name="Quantidade de Vagas")
    valor_inscricao = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Taxa de Inscrição"
    )
    edital = models.ForeignKey(
        Edital, related_name="niveis_selecao", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Nível de Seleção"
        verbose_name_plural = "Níveis de Seleção"


class Documento(models.Model):
    nome = models.CharField(max_length=255)
    categoria = models.CharField(
        max_length=255, choices=CategoriaDocumentoChoices.choices()
    )
    arquivo = models.FileField(
        help_text="Será aceito arquivo com tamanho máximo 2MB e que seja do tipo: "
        + ", ".join(DOCUMENT_EXTENSIONS)
        + ".",
        validators=[
            FileValidator(
                max_size=2 * 1024 * 1024, allowed_extensions=DOCUMENT_EXTENSIONS
            )
        ],
        blank=True,
        null=True,
    )
    data_upload = models.DateField(verbose_name="Data de upload", auto_now_add=True)
    atualizado_em = models.DateField(verbose_name="Data de atualização", auto_now=True)
    edital = models.ForeignKey(
        Edital, related_name="documentos", on_delete=models.CASCADE
    )
    link_arquivo_externo = models.URLField(
        verbose_name="URL de arquivo externo", null=True, blank=True
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Anexo"
        verbose_name_plural = "Anexos"

    def clean(self):
        msg_arquivo = (
            "Você deve escolher entre definir um arquivo ou um link de arquivo externo."
        )
        if self.arquivo and self.link_arquivo_externo:
            raise ValidationError(msg_arquivo)
        elif not self.arquivo and not self.link_arquivo_externo:
            raise ValidationError(msg_arquivo)


class Cronograma(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome do Período")
    tipo = models.CharField(
        max_length=255, choices=CronogramaChoices.choices(), null=True, blank=True
    )
    inicio = models.DateField(verbose_name="Início")
    fim = models.DateField("Fim")
    inscricao = models.BooleanField(verbose_name="Inscrição", default=False)

    class Meta:
        verbose_name = "Cronograma"
        verbose_name_plural = "Cronogramas"
        ordering = ["inicio", "fim"]

    def __str__(self):
        return "{0.nome} - {0.inicio} à {0.fim}".format(self)

    def is_vigente(self):
        return self.inicio <= datetime.date.today() <= self.fim

    def is_encerrado(self):
        return datetime.date.today() > self.fim


class PeriodoSelecao(Cronograma):
    edital = models.ForeignKey(
        Edital, related_name="cronogramas_selecao", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Cronograma de Seleçao"
        verbose_name_plural = "Cronogramas"


class PeriodoConvocacao(Cronograma):
    evento = models.CharField(max_length=255, choices=EventoCronogramaChoices.choices())
    etapa = models.ForeignKey(
        Etapa, related_name="cronogramas_convocacao", on_delete=models.CASCADE
    )
    gerenciavel = models.BooleanField(
        "Gerenciar via Portal",
        help_text="Assinale essa opção caso deseje que o sistema gerencie a fase",
    )

    class Meta:
        verbose_name = "Período Convocação"
        verbose_name_plural = "Períodos Convocações"

    def is_manifestacao_interesse(self):
        return self.evento == EventoCronogramaChoices.INTERESSE.name
