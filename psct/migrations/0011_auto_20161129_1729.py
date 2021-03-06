# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2016-11-29 17:29
from __future__ import unicode_literals

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import psct.models.inscricao


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("psct", "0010_auto_20161121_0847"),
    ]

    operations = [
        migrations.CreateModel(
            name="FaseAjustePontuacao",
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
                    "data_cadastro",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data do Cadastro"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data da Atualização"
                    ),
                ),
                ("data_inicio", models.DateTimeField(verbose_name="Data de Início")),
                (
                    "data_encerramento",
                    models.DateTimeField(verbose_name="Data de encerramento"),
                ),
                (
                    "avaliadores",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="fase_pontuacao_avaliadores",
                        to="psct.GrupoEdital",
                        verbose_name="Grupo de Avaliadores",
                    ),
                ),
                (
                    "fase_analise",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ajuste_pontuacao",
                        to="psct.FaseAnalise",
                        verbose_name="Fase de Analise",
                    ),
                ),
                (
                    "homologadores",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="fase_pontuacao_homologadores",
                        to="psct.GrupoEdital",
                        verbose_name="Grupo de Homologadores",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Fases de Ajuste de Pontuação",
                "verbose_name": "Fase de Ajuste de Pontuação",
            },
        ),
        migrations.CreateModel(
            name="MailboxPontuacaoAvaliador",
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
                    "data_cadastro",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data do Cadastro"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data da Atualização"
                    ),
                ),
                (
                    "avaliador",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="mailbox_pontuacao_avaliador",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Avaliador",
                    ),
                ),
                (
                    "fase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="mailbox_pontuacao_avaliador",
                        to="psct.FaseAjustePontuacao",
                        verbose_name="Fase de Ajuste de Pontuação",
                    ),
                ),
                (
                    "inscricoes",
                    models.ManyToManyField(
                        related_name="mailbox_pontuacao_avaliador",
                        to="psct.InscricaoPreAnalise",
                        verbose_name="Inscrições",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Caixas de Pontuação do Avaliador",
                "verbose_name": "Caixa de Pontuação do Avaliador",
            },
        ),
        migrations.CreateModel(
            name="MailboxPontuacaoHomologador",
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
                    "data_cadastro",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data do Cadastro"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data da Atualização"
                    ),
                ),
                (
                    "fase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="mailbox_pontuacao_homologador",
                        to="psct.FaseAjustePontuacao",
                        verbose_name="Fase de Ajuste de Pontuação",
                    ),
                ),
                (
                    "homologador",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="mailbox_pontuacao_homologador",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Homologador",
                    ),
                ),
                (
                    "inscricoes",
                    models.ManyToManyField(
                        related_name="mailbox_pontuacao_homologador",
                        to="psct.InscricaoPreAnalise",
                        verbose_name="Inscrições",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Caixas de Pontuação do Homologador",
                "verbose_name": "Caixa de Pontuação do Homologador",
            },
        ),
        migrations.CreateModel(
            name="NotaAnualAvaliador",
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
                    "data_cadastro",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data do Cadastro"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data da Atualização"
                    ),
                ),
                (
                    "ano",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (0, "Supletivo/Enem/Outros"),
                            (6, 6),
                            (7, 7),
                            (8, 8),
                            (1, 1),
                            (2, 2),
                        ],
                        verbose_name="Ano",
                    ),
                ),
                (
                    "portugues",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Português",
                    ),
                ),
                (
                    "matematica",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Matemática",
                    ),
                ),
                (
                    "historia",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="História",
                    ),
                ),
                (
                    "geografia",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Geografia",
                    ),
                ),
            ],
            options={
                "ordering": ("ano",),
                "verbose_name_plural": "Notas Anuais de Avaliadores",
                "verbose_name": "Nota Anual Avaliador",
            },
        ),
        migrations.CreateModel(
            name="NotaAnualHomologador",
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
                    "data_cadastro",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data do Cadastro"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data da Atualização"
                    ),
                ),
                (
                    "ano",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (0, "Supletivo/Enem/Outros"),
                            (6, 6),
                            (7, 7),
                            (8, 8),
                            (1, 1),
                            (2, 2),
                        ],
                        verbose_name="Ano",
                    ),
                ),
                (
                    "portugues",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Português",
                    ),
                ),
                (
                    "matematica",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Matemática",
                    ),
                ),
                (
                    "historia",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="História",
                    ),
                ),
                (
                    "geografia",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Geografia",
                    ),
                ),
            ],
            options={
                "ordering": ("ano",),
                "verbose_name_plural": "Notas Anuais de Homologadores",
                "verbose_name": "Nota Anual Homologador",
            },
        ),
        migrations.CreateModel(
            name="PilhaInscricaoAjuste",
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
                    "data_cadastro",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data do Cadastro"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data da Atualização"
                    ),
                ),
                (
                    "fase",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pilha",
                        to="psct.FaseAjustePontuacao",
                        verbose_name="Fase de Ajuste",
                    ),
                ),
                (
                    "inscricoes",
                    models.ManyToManyField(
                        to="psct.InscricaoPreAnalise", verbose_name="Inscrições"
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Pilhas de Inscrições para ajuste",
                "verbose_name": "Pilha de Inscrição para Ajuste",
            },
        ),
        migrations.CreateModel(
            name="PontuacaoAvaliador",
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
                    "data_cadastro",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data do Cadastro"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data da Atualização"
                    ),
                ),
                (
                    "valor",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Valor",
                    ),
                ),
                (
                    "valor_pt",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Valor de desempate PT",
                    ),
                ),
                (
                    "valor_mt",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Valor de desempate MT",
                    ),
                ),
                (
                    "ensino_regular",
                    models.BooleanField(
                        default=True, verbose_name="Candidato cursou o ensino regular?"
                    ),
                ),
                (
                    "concluida",
                    models.CharField(
                        choices=[("", "--------"), ("NAO", "Não"), ("SIM", "Sim")],
                        help_text="A pontuação não poderá mais ser editada e será entregue ao homologador após o envio.",
                        max_length=5,
                        verbose_name="Enviar avaliação",
                    ),
                ),
                (
                    "avaliador",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pontuacoes_avaliadores",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Avaliador",
                    ),
                ),
                (
                    "fase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pontuacoes_avaliadores",
                        to="psct.FaseAjustePontuacao",
                        verbose_name="Fase de Ajuste de Pontuação",
                    ),
                ),
                (
                    "inscricao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pontuacoes_avaliadores",
                        to="psct.Inscricao",
                        verbose_name="Inscrição",
                    ),
                ),
                (
                    "inscricao_preanalise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pontuacoes_avaliadores",
                        to="psct.InscricaoPreAnalise",
                        verbose_name="Inscrição Pré-Análise",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Pontuações de Avaliadores",
                "verbose_name": "Pontuação Avaliador",
            },
            bases=(models.Model, psct.models.inscricao.PontuacaoBase),
        ),
        migrations.CreateModel(
            name="PontuacaoHomologador",
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
                    "data_cadastro",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data do Cadastro"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data da Atualização"
                    ),
                ),
                (
                    "valor",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Valor",
                    ),
                ),
                (
                    "valor_pt",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Valor de desempate PT",
                    ),
                ),
                (
                    "valor_mt",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Valor de desempate MT",
                    ),
                ),
                (
                    "ensino_regular",
                    models.BooleanField(
                        default=True, verbose_name="Candidato cursou o ensino regular?"
                    ),
                ),
                (
                    "fase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pontuacoes_homologadores",
                        to="psct.FaseAjustePontuacao",
                        verbose_name="Fase de Ajuste de Pontuação",
                    ),
                ),
                (
                    "homologador",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pontuacoes_homologadores",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Homologador",
                    ),
                ),
                (
                    "inscricao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pontuacoes_homologadores",
                        to="psct.Inscricao",
                        verbose_name="Inscrição",
                    ),
                ),
                (
                    "inscricao_preanalise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pontuacoes_homologadores",
                        to="psct.InscricaoPreAnalise",
                        verbose_name="Inscrição Pré-Análise",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Pontuações de Homologadores",
                "verbose_name": "Pontuação Homologador",
            },
            bases=(models.Model, psct.models.inscricao.PontuacaoBase),
        ),
        migrations.AddField(
            model_name="notaanualhomologador",
            name="pontuacao",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="notas",
                to="psct.PontuacaoHomologador",
                verbose_name="Pontuação da Inscrição",
            ),
        ),
        migrations.AddField(
            model_name="notaanualavaliador",
            name="pontuacao",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="notas",
                to="psct.PontuacaoAvaliador",
                verbose_name="Pontuação da Inscrição",
            ),
        ),
    ]
