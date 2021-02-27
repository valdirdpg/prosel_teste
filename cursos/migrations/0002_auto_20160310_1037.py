# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-03-10 10:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cursos", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="campus",
            name="mapa",
            field=models.CharField(
                blank=True,
                help_text='Endereço da opção "Incorporar Mapa" do Google Maps. Veja este tutorial de como\n                                         fazer: https://support.google.com/maps/answer/3544418?hl=pt-BR',
                max_length=1025,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="tipodocumento",
            name="obrigatorio",
            field=models.BooleanField(
                default=False,
                help_text="Ao marcar este campo, você exige que o coordenador do curso cadastre\n                                                   pelo menos um documento deste tipo.",
                verbose_name="Obrigatório",
            ),
        ),
    ]
