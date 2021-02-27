# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-10-04 16:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cursos", "0022_auto_20170607_1810"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cursonocampus",
            name="modalidade",
            field=models.CharField(
                choices=[
                    ("PRESENCIAL", "Presencial"),
                    ("EAD", "A distância"),
                    ("SEMIPRESENCIAL", "Semipresencial"),
                ],
                max_length=16,
            ),
        ),
    ]
