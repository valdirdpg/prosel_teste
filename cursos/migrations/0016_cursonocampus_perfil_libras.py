# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2016-12-14 15:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cursos", "0015_auto_20161020_1459"),
    ]

    operations = [
        migrations.AddField(
            model_name="cursonocampus",
            name="perfil_libras",
            field=models.URLField(
                blank=True,
                help_text='Endereço "src" que aparece na opção de compartilhamento "Incorporar" do YouTube.',
                null=True,
                verbose_name="URL de vídeo em Libras do Perfil Profissional",
            ),
        ),
    ]
