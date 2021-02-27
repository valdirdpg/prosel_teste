# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-31 16:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("processoseletivo", "0008_auto_20170127_1654"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="inscricao",
            options={
                "ordering": ("desempenho__classificacao",),
                "verbose_name": "Inscrição",
                "verbose_name_plural": "Inscrições",
            },
        ),
        migrations.RemoveField(model_name="inscricao", name="chamada",),
        migrations.AddField(
            model_name="inscricao",
            name="chamada",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="inscricoes",
                to="processoseletivo.Chamada",
                verbose_name="Chamada",
            ),
        ),
    ]