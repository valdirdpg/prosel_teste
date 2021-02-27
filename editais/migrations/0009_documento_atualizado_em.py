# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-17 11:49
from __future__ import unicode_literals

from django.db import migrations, models


def definir_data_atualizacao(apps, schema_editor):
    Documento = apps.get_model("editais", "Documento")
    for d in Documento.objects.all():
        d.atualizado_em = d.data_upload
        d.save()


class Migration(migrations.Migration):

    dependencies = [
        ("editais", "0008_auto_20170419_1339"),
    ]

    operations = [
        migrations.AddField(
            model_name="documento",
            name="atualizado_em",
            field=models.DateField(
                blank=True, null=True, verbose_name="Data de atualização"
            ),
        ),
        migrations.RunPython(definir_data_atualizacao, definir_data_atualizacao),
    ]