# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-17 15:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("editais", "0006_periodoconvocacao_gerenciavel"),
    ]

    operations = [
        migrations.AlterField(
            model_name="edital",
            name="edicao",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="processoseletivo.Edicao",
                verbose_name="Edição de Processo Seletivo",
            ),
        ),
    ]
