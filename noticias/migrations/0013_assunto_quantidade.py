# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-26 10:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("noticias", "0012_auto_20170420_1134"),
    ]

    operations = [
        migrations.AddField(
            model_name="assunto",
            name="quantidade",
            field=models.IntegerField(
                default=3,
                help_text="Informe um número maior que zero e múltiplo de 3. Ex.: 3, 6, 9, etc.",
                verbose_name="Quantidade de notícias exibidas",
            ),
        ),
    ]
