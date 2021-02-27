# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-10-11 17:00
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
        ("psct", "0004_unaccent"),
    ]

    operations = [
        migrations.CreateModel(
            name="Coluna",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nome",
                    models.CharField(
                        max_length=255, verbose_name="Nome do atributo da entidade"
                    ),
                ),
                (
                    "query_string",
                    models.CharField(
                        max_length=255,
                        verbose_name="Query String de acesso ao atributo",
                    ),
                ),
                (
                    "aggregate",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Sum", "Soma"),
                            ("Avg", "Média"),
                            ("Count", "Quantidade"),
                            ("Unaccent", "Remover acentos"),
                        ],
                        max_length=255,
                        null=True,
                        verbose_name="Aplicar função",
                    ),
                ),
                (
                    "aggregate_nome",
                    models.CharField(
                        max_length=255, verbose_name="Nome da coluna do aggregate"
                    ),
                ),
                (
                    "entidade",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.ContentType",
                        verbose_name="Entidade",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Colunas",
                "verbose_name": "Coluna",
                "ordering": ("nome",),
            },
        ),
        migrations.CreateModel(
            name="ColunaConsulta",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "posicao",
                    models.SmallIntegerField(
                        choices=[
                            (1, 1),
                            (2, 2),
                            (3, 3),
                            (4, 4),
                            (5, 5),
                            (6, 6),
                            (7, 7),
                            (8, 8),
                            (9, 9),
                            (10, 10),
                            (11, 11),
                            (12, 12),
                            (13, 13),
                            (14, 14),
                            (15, 15),
                            (16, 16),
                            (17, 17),
                            (18, 18),
                            (19, 19),
                            (20, 20),
                            (21, 21),
                            (22, 22),
                            (23, 23),
                            (24, 24),
                            (25, 25),
                            (26, 26),
                            (27, 27),
                            (28, 28),
                            (29, 29),
                            (30, 30),
                            (31, 31),
                            (32, 32),
                            (33, 33),
                            (34, 34),
                            (35, 35),
                            (36, 36),
                            (37, 37),
                            (38, 38),
                            (39, 39),
                            (40, 40),
                            (41, 41),
                            (42, 42),
                            (43, 43),
                            (44, 44),
                            (45, 45),
                            (46, 46),
                            (47, 47),
                            (48, 48),
                            (49, 49),
                            (50, 50),
                            (51, 51),
                            (52, 52),
                            (53, 53),
                            (54, 54),
                            (55, 55),
                            (56, 56),
                            (57, 57),
                            (58, 58),
                            (59, 59),
                            (60, 60),
                            (61, 61),
                            (62, 62),
                            (63, 63),
                            (64, 64),
                            (65, 65),
                            (66, 66),
                            (67, 67),
                            (68, 68),
                            (69, 69),
                            (70, 70),
                            (71, 71),
                            (72, 72),
                            (73, 73),
                            (74, 74),
                            (75, 75),
                            (76, 76),
                            (77, 77),
                            (78, 78),
                            (79, 79),
                            (80, 80),
                            (81, 81),
                            (82, 82),
                            (83, 83),
                            (84, 84),
                            (85, 85),
                            (86, 86),
                            (87, 87),
                            (88, 88),
                            (89, 89),
                            (90, 90),
                            (91, 91),
                            (92, 92),
                            (93, 93),
                            (94, 94),
                            (95, 95),
                            (96, 96),
                            (97, 97),
                            (98, 98),
                            (99, 99),
                        ],
                        verbose_name="Posição",
                    ),
                ),
                (
                    "nome",
                    models.CharField(
                        blank=True,
                        help_text="Opcional. Nome da coluna será usada como padrão",
                        max_length=255,
                        null=True,
                        verbose_name="Nome da coluna na consulta",
                    ),
                ),
                (
                    "coluna",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="psct.Coluna",
                        verbose_name="Coluna",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Colunas da Consultas",
                "verbose_name": "Coluna da Consulta",
                "ordering": ("posicao",),
            },
        ),
        migrations.CreateModel(
            name="Consulta",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nome",
                    models.CharField(max_length=255, verbose_name="Nome da consulta"),
                ),
                (
                    "data_criacao",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data da criação"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data da atualização"
                    ),
                ),
                (
                    "itens_por_pagina",
                    models.PositiveIntegerField(
                        default=10,
                        help_text="Limite máximo de 50 itens.",
                        verbose_name="Quantidade de Itens por Página",
                    ),
                ),
                (
                    "compartilhar",
                    models.BooleanField(
                        default=False,
                        verbose_name="Compartilhar consulta com outros usuários?",
                    ),
                ),
                (
                    "entidade",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.ContentType",
                        verbose_name="Entidade",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Usuário",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Consultas",
                "permissions": (("view_consulta", "Administrador pode ver consulta"),),
                "verbose_name": "Consulta",
                "ordering": ("nome",),
            },
        ),
        migrations.CreateModel(
            name="Email",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("assunto", models.CharField(max_length=255, verbose_name="Assunto")),
                ("conteudo", models.TextField(verbose_name="Conteúdo")),
                (
                    "data_criacao",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data da criação"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data da atualização"
                    ),
                ),
                (
                    "destinatarios",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="psct.Consulta",
                        verbose_name="Destinatários",
                    ),
                ),
            ],
            options={"verbose_name_plural": "Emails", "verbose_name": "Email",},
        ),
        migrations.CreateModel(
            name="Filtro",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nome",
                    models.CharField(
                        max_length=255, unique=True, verbose_name="Nome do filtro"
                    ),
                ),
                (
                    "query_string",
                    models.CharField(max_length=255, verbose_name="Query String"),
                ),
            ],
            options={
                "verbose_name_plural": "Filtros",
                "verbose_name": "Filtro",
                "ordering": ("nome",),
            },
        ),
        migrations.CreateModel(
            name="OrdenacaoConsulta",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "posicao",
                    models.SmallIntegerField(
                        choices=[
                            (1, 1),
                            (2, 2),
                            (3, 3),
                            (4, 4),
                            (5, 5),
                            (6, 6),
                            (7, 7),
                            (8, 8),
                            (9, 9),
                            (10, 10),
                            (11, 11),
                            (12, 12),
                            (13, 13),
                            (14, 14),
                            (15, 15),
                            (16, 16),
                            (17, 17),
                            (18, 18),
                            (19, 19),
                            (20, 20),
                            (21, 21),
                            (22, 22),
                            (23, 23),
                            (24, 24),
                            (25, 25),
                            (26, 26),
                            (27, 27),
                            (28, 28),
                            (29, 29),
                            (30, 30),
                            (31, 31),
                            (32, 32),
                            (33, 33),
                            (34, 34),
                            (35, 35),
                            (36, 36),
                            (37, 37),
                            (38, 38),
                            (39, 39),
                            (40, 40),
                            (41, 41),
                            (42, 42),
                            (43, 43),
                            (44, 44),
                            (45, 45),
                            (46, 46),
                            (47, 47),
                            (48, 48),
                            (49, 49),
                            (50, 50),
                            (51, 51),
                            (52, 52),
                            (53, 53),
                            (54, 54),
                            (55, 55),
                            (56, 56),
                            (57, 57),
                            (58, 58),
                            (59, 59),
                            (60, 60),
                            (61, 61),
                            (62, 62),
                            (63, 63),
                            (64, 64),
                            (65, 65),
                            (66, 66),
                            (67, 67),
                            (68, 68),
                            (69, 69),
                            (70, 70),
                            (71, 71),
                            (72, 72),
                            (73, 73),
                            (74, 74),
                            (75, 75),
                            (76, 76),
                            (77, 77),
                            (78, 78),
                            (79, 79),
                            (80, 80),
                            (81, 81),
                            (82, 82),
                            (83, 83),
                            (84, 84),
                            (85, 85),
                            (86, 86),
                            (87, 87),
                            (88, 88),
                            (89, 89),
                            (90, 90),
                            (91, 91),
                            (92, 92),
                            (93, 93),
                            (94, 94),
                            (95, 95),
                            (96, 96),
                            (97, 97),
                            (98, 98),
                            (99, 99),
                        ],
                        verbose_name="Posição",
                    ),
                ),
                (
                    "ordem",
                    models.SmallIntegerField(
                        choices=[(0, "Crescente"), (1, "Decrescente")],
                        default=0,
                        verbose_name="Ordem",
                    ),
                ),
                (
                    "coluna",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="psct.Coluna",
                        verbose_name="Coluna",
                    ),
                ),
                (
                    "consulta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ordenacoes",
                        to="psct.Consulta",
                        verbose_name="Consulta",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Ordenações da Consulta",
                "verbose_name": "Ordenação da Consulta",
                "ordering": ("posicao",),
            },
        ),
        migrations.CreateModel(
            name="RegraBase",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "valor",
                    models.CharField(
                        max_length=255, verbose_name="Valor de comparação"
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Filtros de Busca",
                "verbose_name": "Filtro de Busca",
            },
        ),
        migrations.CreateModel(
            name="SolicitacaoEnvioEmail",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "data",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data da solicitação"
                    ),
                ),
                (
                    "sucesso",
                    models.BooleanField(default=False, verbose_name="Sucesso?"),
                ),
                (
                    "email",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="psct.Email",
                        verbose_name="email",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Usuário",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Solicitações de Envio de Email",
                "verbose_name": "Solicitação de Envio de Email",
            },
        ),
        migrations.CreateModel(
            name="RegraExclusao",
            fields=[
                (
                    "regrabase_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="psct.RegraBase",
                    ),
                ),
                (
                    "consulta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="exclusoes",
                        to="psct.Consulta",
                        verbose_name="Consulta",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Regras de Exclusão",
                "verbose_name": "Regra de Exclusão",
            },
            bases=("psct.regrabase",),
        ),
        migrations.CreateModel(
            name="RegraFiltro",
            fields=[
                (
                    "regrabase_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="psct.RegraBase",
                    ),
                ),
                (
                    "consulta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="filtros",
                        to="psct.Consulta",
                        verbose_name="Consulta",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Regras de Filtros",
                "verbose_name": "Regra de Filtro",
            },
            bases=("psct.regrabase",),
        ),
        migrations.AddField(
            model_name="regrabase",
            name="coluna",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="psct.Coluna",
                verbose_name="Campo da entidade",
            ),
        ),
        migrations.AddField(
            model_name="regrabase",
            name="filtro",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="psct.Filtro",
                verbose_name="Filtro",
            ),
        ),
        migrations.AddField(
            model_name="colunaconsulta",
            name="consulta",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="colunas",
                to="psct.Consulta",
                verbose_name="Consulta",
            ),
        ),
    ]
