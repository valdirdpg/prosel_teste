# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-09-18 16:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("processoseletivo", "0018_auto_20170607_1501"),
    ]

    operations = [
        migrations.AddField(
            model_name="registrotransicaomodalidadevagas",
            name="atualizado_em",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name="registrotransicaomodalidadevagas",
            name="criado_em",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
