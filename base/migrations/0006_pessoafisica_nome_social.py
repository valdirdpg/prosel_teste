# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-13 12:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0005_auto_20170127_1643"),
    ]

    operations = [
        migrations.AddField(
            model_name="pessoafisica",
            name="nome_social",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="Nome Social"
            ),
        ),
    ]
