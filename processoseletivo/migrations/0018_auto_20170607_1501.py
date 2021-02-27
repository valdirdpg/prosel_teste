# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-07 15:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("processoseletivo", "0017_auto_20170519_1558"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="analisedocumental",
            options={
                "ordering": ["confirmacao_interesse__inscricao__candidato"],
                "verbose_name": "Análise de Documentos",
                "verbose_name_plural": "Análises de Documentos",
            },
        ),
        migrations.AlterModelOptions(
            name="confirmacaointeresse",
            options={
                "ordering": ["inscricao__candidato"],
                "verbose_name": "Confirmação de Interesse",
                "verbose_name_plural": "Confirmações de Interesse",
            },
        ),
        migrations.AlterModelOptions(
            name="recurso",
            options={
                "ordering": [
                    "analise_documental__confirmacao_interesse__inscricao__candidato"
                ],
                "verbose_name": "Recurso",
                "verbose_name_plural": "Recursos",
            },
        ),
        migrations.AlterModelOptions(
            name="tipoanalise",
            options={
                "ordering": ["pk"],
                "verbose_name": "Tipo de análise de documento",
                "verbose_name_plural": "Tipos de análise de documento",
            },
        ),
        migrations.AlterField(
            model_name="analisedocumental",
            name="confirmacao_interesse",
            field=models.OneToOneField(
                help_text="Informe o nome do candidato. Somente aqueles que confirmaram interesse.",
                on_delete=django.db.models.deletion.CASCADE,
                to="processoseletivo.ConfirmacaoInteresse",
                verbose_name="Confirmação de interesse",
            ),
        ),
        migrations.AlterField(
            model_name="avaliacaodocumental",
            name="observacao",
            field=models.TextField(
                blank=True,
                help_text="Informe aqui caso o avaliador tenha registrado alguma observação sobre sobre a avaliação.",
                max_length=255,
                verbose_name="Observação",
            ),
        ),
        migrations.AlterField(
            model_name="recurso",
            name="analise_documental",
            field=models.OneToOneField(
                help_text="Informe o nome do candidato. Somente aqueles que possuem análise documental.",
                on_delete=django.db.models.deletion.CASCADE,
                to="processoseletivo.AnaliseDocumental",
                verbose_name="Análise documental",
            ),
        ),
    ]
