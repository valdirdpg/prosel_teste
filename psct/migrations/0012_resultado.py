# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2016-12-12 10:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import psct.models.resultado


class Migration(migrations.Migration):

    dependencies = [
        ("cursos", "0015_auto_20161020_1459"),
        ("editais", "0004_auto_20161013_1651"),
        ("psct", "0011_auto_20161129_1729"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResultadoFinal",
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
                    "edital",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="resultado",
                        to="editais.Edital",
                        verbose_name="Edital",
                    ),
                ),
            ],
            options={
                "verbose_name": "Resultado Final",
                "verbose_name_plural": "Resultados Final",
            },
        ),
        migrations.CreateModel(
            name="ResultadoPreliminar",
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
                        related_name="resultados_preliminares",
                        to="psct.FaseAnalise",
                        verbose_name="Fase de Análise",
                    ),
                ),
            ],
            options={
                "verbose_name": "Resultado Preliminar",
                "verbose_name_plural": "Resultados preliminares",
            },
        ),
        migrations.CreateModel(
            name="ResultadoPreliminarCurso",
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
                    "curso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="cursos.CursoNoCampus",
                        verbose_name="Curso",
                    ),
                ),
                (
                    "resultado",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cursos",
                        to="psct.ResultadoPreliminar",
                        verbose_name="Resultado Preliminar",
                    ),
                ),
            ],
            options={
                "verbose_name": "Resultado preliminnar de curso",
                "verbose_name_plural": "Resultados preliminar de cursos",
                "ordering": ("curso__curso__nome",),
            },
        ),
        migrations.CreateModel(
            name="ResultadoPreliminarHomologado",
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
                    "edital",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="resultado_preliminar",
                        to="editais.Edital",
                        verbose_name="Edital",
                    ),
                ),
                (
                    "resultado",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="psct.ResultadoPreliminar",
                        verbose_name="Resultado",
                    ),
                ),
            ],
            options={
                "verbose_name": "Resultado Preliminar Homologado",
                "verbose_name_plural": "Resultados preliminares homologados",
            },
        ),
        migrations.CreateModel(
            name="ResultadoPreliminarInscricao",
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
                    "classificacao",
                    models.IntegerField(verbose_name="Classificação Geral"),
                ),
                (
                    "classificacao_cota",
                    models.IntegerField(
                        blank=True, null=True, verbose_name="Classificação na cota"
                    ),
                ),
                (
                    "inscricao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="resultados_preliminares",
                        to="psct.Inscricao",
                        verbose_name="Inscrição",
                    ),
                ),
                (
                    "inscricao_preanalise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="resultados_preliminares",
                        to="psct.InscricaoPreAnalise",
                        verbose_name="Inscrição Pré-análise",
                    ),
                ),
                (
                    "justiticativa_indeferimento",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="psct.JustificativaIndeferimento",
                        verbose_name="Justificativa do Indeferimento",
                    ),
                ),
                (
                    "resultado_curso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inscricoes",
                        to="psct.ResultadoPreliminarCurso",
                        verbose_name="Resultado Preliminar Curso",
                    ),
                ),
            ],
            options={
                "verbose_name": "Resultado preliminar inscrição",
                "verbose_name_plural": "Resultados preliminares inscrição",
                "ordering": ("classificacao",),
            },
        ),
        migrations.CreateModel(
            name="ResultadoPreliminarInscricaoIndeferida",
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
                    "inscricao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="psct.Inscricao",
                        verbose_name="Inscrição",
                    ),
                ),
                (
                    "inscricao_preanalise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="psct.InscricaoPreAnalise",
                        verbose_name="Inscrição Pré-análise",
                    ),
                ),
                (
                    "justiticativa_indeferimento",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="psct.JustificativaIndeferimento",
                        verbose_name="Justificativa do Indeferimento",
                    ),
                ),
                (
                    "resultado",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inscricoes_indeferidas",
                        to="psct.ResultadoPreliminar",
                        verbose_name="Resultado Preliminar",
                    ),
                ),
            ],
            options={
                "verbose_name": "Resultado prel. inscrição indeferida",
                "verbose_name_plural": "Resultados prel. inscrição indeferida",
            },
        ),
        migrations.CreateModel(
            name="VagasResultadoPreliminar",
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
                    "quantidade",
                    models.IntegerField(default=0, verbose_name="Quantidade"),
                ),
                (
                    "modalidade",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="psct.Modalidade",
                        verbose_name="Modalidade",
                    ),
                ),
                (
                    "resultado_curso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vagas",
                        to="psct.ResultadoPreliminarCurso",
                        verbose_name="Resultado Preliminar Curso",
                    ),
                ),
            ],
            options={
                "verbose_name": "Vagas do resultado preliminar",
                "verbose_name_plural": "Vagas dos resultados preliminares",
            },
        ),
        migrations.AddField(
            model_name="processoinscricao",
            name="data_resultado_preliminar",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Data a partir de quando o candidato poderá visualizar o resultado preliminar",
            ),
        ),
        migrations.AddField(
            model_name="resultadofinal",
            name="resultado",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="psct.ResultadoPreliminar",
                verbose_name="Resultado",
            ),
        ),
    ]