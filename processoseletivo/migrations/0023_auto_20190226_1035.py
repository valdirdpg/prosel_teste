# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2019-02-26 10:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("processoseletivo", "0022_auto_20180222_1711"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tipoanalise",
            name="modalidade",
            field=models.ManyToManyField(
                related_name="tipos_analise", to="processoseletivo.Modalidade"
            ),
        ),
    ]