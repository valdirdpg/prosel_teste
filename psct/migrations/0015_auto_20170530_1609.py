# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-30 16:09
from __future__ import unicode_literals

import base.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("psct", "0014_auto_20170419_1339"),
    ]

    operations = [
        migrations.AddField(
            model_name="inscricao",
            name="cpf",
            field=models.CharField(
                max_length=14,
                null=True,
                validators=[base.validators.cpf_validator],
                verbose_name="CPF",
            ),
        ),
        migrations.AddField(
            model_name="inscricao",
            name="nome",
            field=models.CharField(max_length=100, null=True, verbose_name="Nome"),
        ),
    ]
