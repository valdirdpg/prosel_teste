# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-03-21 18:16
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("processoseletivo", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="candidato",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="vaga",
            name="candidato",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="processoseletivo.Candidato",
            ),
        ),
    ]
