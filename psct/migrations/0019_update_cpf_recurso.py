# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-11-19 14:49
from __future__ import unicode_literals

from django.db import migrations


def change_cpf(apps, schema_editor):
    Inscricao = apps.get_model("psct.Inscricao")
    Inscricao.objects.filter(pk=87791).update(candidato_id=79068, cpf="112.412.284-26")
    ComprovanteInscricao = apps.get_model("psct.ComprovanteInscricao")
    ComprovanteInscricao.objects.filter(inscricao_id=87791).delete()


def undo_change_cpf(apps, schema_editor):
    Inscricao = apps.get_model("psct.Inscricao")
    Inscricao.objects.filter(pk=87791).update(candidato_id=96094)


class Migration(migrations.Migration):
    dependencies = [
        ("psct", "0018_change_inscricoes_edital_73_2018"),
    ]

    operations = [migrations.RunPython(change_cpf, undo_change_cpf)]