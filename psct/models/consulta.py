from uuid import uuid4

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.lookups import Unaccent
from django.core.exceptions import FieldError
from django.db import models
from django.urls import reverse

from psct.utils import consulta as utils

CACHED_FORMAT_FIELD = {}


class ConsultaMalFormada(Exception):
    pass


class Coluna(models.Model):
    AGGREGATE_CHOICES = [
        ("Sum", "Soma"),
        ("Avg", "Média"),
        ("Count", "Quantidade"),
        ("Unaccent", "Remover acentos"),
    ]
    AGGREGATE_FUNCS = dict(
        Sum=models.Sum, Avg=models.Avg, Count=models.Count, Unaccent=Unaccent
    )

    entidade = models.ForeignKey(
        ContentType, verbose_name="Entidade", on_delete=models.CASCADE
    )
    nome = models.CharField(max_length=255, verbose_name="Nome do atributo da entidade")
    query_string = models.CharField(
        max_length=255, verbose_name="Query String de acesso ao atributo"
    )
    aggregate = models.CharField(
        max_length=255,
        verbose_name="Aplicar função",
        choices=AGGREGATE_CHOICES,
        null=True,
        blank=True,
    )
    aggregate_nome = models.CharField(
        max_length=255, verbose_name="Nome da coluna do aggregate"
    )

    def __str__(self):
        return f"{self.nome} em {self.entidade}"

    class Meta:
        verbose_name = "Coluna"
        verbose_name_plural = "Colunas"
        ordering = ("nome",)

    def to_django_values(self):
        if self.aggregate:
            return self.aggregate_nome
        return self.query_string

    @property
    def aggregate_value(self):
        key = self.aggregate_nome
        value = self.AGGREGATE_FUNCS[self.aggregate](self.query_string)
        return key, value

    def save(self, *args, **kwargs):
        if not self.id:
            self.aggregate_nome = "field" + uuid4().hex
        super().save(*args, **kwargs)

    def _get_type_key(self):
        return self.entidade, self.query_string

    def get_format(self):
        key = self._get_type_key()
        if key not in CACHED_FORMAT_FIELD:
            CACHED_FORMAT_FIELD[key] = self._format_function()
        return CACHED_FORMAT_FIELD[key]

    def _format_function(self):
        return utils.get_format(self.entidade.model_class(), self.query_string)


class Filtro(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome do filtro", unique=True)
    query_string = models.CharField(max_length=255, verbose_name="Query String")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Filtro"
        verbose_name_plural = "Filtros"
        ordering = ("nome",)


class Consulta(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome da consulta")
    entidade = models.ForeignKey(
        ContentType, verbose_name="Entidade", on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, verbose_name="Usuário", on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(
        verbose_name="Data da criação", auto_now_add=True
    )
    data_atualizacao = models.DateTimeField(
        verbose_name="Data da atualização", auto_now=True
    )
    itens_por_pagina = models.PositiveIntegerField(
        verbose_name="Quantidade de Itens por Página",
        default=10,
        help_text="Limite máximo de 50 itens.",
    )
    compartilhar = models.BooleanField(
        verbose_name="Compartilhar consulta com outros usuários?", default=False
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas"
        ordering = ("nome",)

    def get_absolute_url(self):
        return reverse("visualizar_consulta_psct", kwargs=dict(pk=self.pk))

    @property
    def consulta_queryset(self):
        filtros = dict([filtro.to_django_filter() for filtro in self.filtros.all()])
        excludes = dict(
            [exclusao.to_django_filter() for exclusao in self.exclusoes.all()]
        )
        colunas = [coluna.to_django_values() for coluna in self.colunas.all()]

        annotates = set()
        colunas_annotate = [
            coluna_consulta.coluna
            for coluna_consulta in self.colunas.filter(coluna__aggregate__isnull=False)
        ]
        for coluna in colunas_annotate:
            annotates.add(coluna)

        filtros_annotate = [
            filtro.coluna
            for filtro in self.filtros.filter(coluna__aggregate__isnull=False)
        ]
        for coluna in filtros_annotate:
            annotates.add(coluna)

        exclusoes_annotate = [
            exclusao.coluna
            for exclusao in self.exclusoes.filter(coluna__aggregate__isnull=False)
        ]
        for coluna in exclusoes_annotate:
            annotates.add(coluna)

        ordenacoes = [
            ordenacao.to_django_order() for ordenacao in self.ordenacoes.all()
        ]

        annotates = dict([coluna.aggregate_value for coluna in annotates])

        qs = self.entidade.model_class().objects.all()

        try:
            if filtros:
                qs = qs.filter(**filtros)

            if excludes:
                qs = qs.exclude(**excludes)

            if annotates:
                qs = qs.annotate(**annotates)

            if ordenacoes:
                qs = qs.order_by(*ordenacoes)

            return qs.distinct().values_list(*colunas)
        except (TypeError, FieldError) as error:
            raise ConsultaMalFormada("Erro na construção da consulta")

    @property
    def colunas_label(self):
        return self.colunas.order_by("posicao")

    def get_format_for_coluna(self, index):
        if not hasattr(self, "_coluna_cache"):
            self._coluna_cache = [c.format() for c in self.colunas_label]
        return self._coluna_cache[index]

    def test_query(self):
        return self.consulta_queryset[:10]


class RegraBase(models.Model):

    coluna = models.ForeignKey(
        Coluna, verbose_name="Campo da entidade", on_delete=models.CASCADE
    )
    filtro = models.ForeignKey(Filtro, verbose_name="Filtro", on_delete=models.CASCADE)
    valor = models.CharField(max_length=255, verbose_name="Valor de comparação")

    def __str__(self):
        return "{}__{}=".format(
            self.coluna.query_string, self.filtro.query_string, self.valor
        )

    class Meta:
        verbose_name = "Filtro de Busca"
        verbose_name_plural = "Filtros de Busca"

    def to_django_filter(self):
        key = f"{self.coluna.query_string}__{self.filtro.query_string}"
        return key, self.get_valor()

    def get_valor(self):
        if self.valor == "True":
            return True
        elif self.valor == "False":
            return False
        return self.valor


class RegraFiltro(RegraBase):
    consulta = models.ForeignKey(
        Consulta,
        verbose_name="Consulta",
        on_delete=models.CASCADE,
        related_name="filtros",
    )

    class Meta:
        verbose_name_plural = "Regras de Filtros"
        verbose_name = "Regra de Filtro"


class RegraExclusao(RegraBase):
    consulta = models.ForeignKey(
        Consulta,
        verbose_name="Consulta",
        on_delete=models.CASCADE,
        related_name="exclusoes",
    )

    class Meta:
        verbose_name_plural = "Regras de Exclusão"
        verbose_name = "Regra de Exclusão"


class ColunaConsulta(models.Model):
    consulta = models.ForeignKey(
        Consulta,
        verbose_name="Consulta",
        related_name="colunas",
        on_delete=models.CASCADE,
    )

    posicao = models.SmallIntegerField(
        verbose_name="Posição", choices=[(x, x) for x in range(1, 100)]
    )
    coluna = models.ForeignKey(Coluna, verbose_name="Coluna", on_delete=models.CASCADE)
    nome = models.CharField(
        verbose_name="Nome da coluna na consulta",
        max_length=255,
        null=True,
        blank=True,
        help_text="Opcional. Nome da coluna será usada como padrão",
    )

    class Meta:
        verbose_name = "Coluna da Consulta"
        verbose_name_plural = "Colunas da Consultas"
        ordering = ("posicao",)

    def to_django_values(self):
        return self.coluna.to_django_values()

    def format(self):
        return self.coluna.get_format()

    def __str__(self):
        return self.nome_display

    @property
    def nome_display(self):
        if not self.nome:
            return self.coluna.nome
        return self.nome


class OrdenacaoConsulta(models.Model):
    ORDEM_CHOICES = ((0, "Crescente"), (1, "Decrescente"))
    consulta = models.ForeignKey(
        Consulta,
        verbose_name="Consulta",
        related_name="ordenacoes",
        on_delete=models.CASCADE,
    )
    posicao = models.SmallIntegerField(
        verbose_name="Posição", choices=[(x, x) for x in range(1, 100)]
    )
    coluna = models.ForeignKey(Coluna, verbose_name="Coluna", on_delete=models.CASCADE)
    ordem = models.SmallIntegerField(
        verbose_name="Ordem", choices=ORDEM_CHOICES, default=0
    )

    class Meta:
        verbose_name = "Ordenação da Consulta"
        verbose_name_plural = "Ordenações da Consulta"
        ordering = ("posicao",)

    def to_django_order(self):
        if self.ordem:
            return "-" + self.coluna.to_django_values()
        return self.coluna.to_django_values()
