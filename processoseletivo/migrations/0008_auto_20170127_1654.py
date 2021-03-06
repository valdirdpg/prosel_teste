# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-27 16:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("processoseletivo", "0007_remove_dados_antigos"),
    ]

    operations = [
        migrations.AlterField(
            model_name="analisedocumental",
            name="confirmacao_interesse",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                to="processoseletivo.ConfirmacaoInteresse",
                verbose_name="Confirmação de interesse",
            ),
        ),
        migrations.AlterField(
            model_name="avaliacaodocumental",
            name="tipo_analise",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tipo_analise",
                to="processoseletivo.TipoAnalise",
                verbose_name="Tipo de análise",
            ),
        ),
        migrations.AlterField(
            model_name="tipoanalise",
            name="nome",
            field=models.CharField(
                max_length=255, unique=True, verbose_name="Tipo de avaliação"
            ),
        ),
        migrations.AlterField(
            model_name="tipoanalise",
            name="setor_responsavel",
            field=models.CharField(max_length=255, verbose_name="Setor responsável"),
        ),
    ]
