# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-09-30 16:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("editais", "0002_auto_20160310_1037"),
    ]

    operations = [
        migrations.AddField(
            model_name="cronograma",
            name="inscricao",
            field=models.BooleanField(default=False, verbose_name="Inscrição"),
        ),
    ]
