# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-19 15:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("psct", "0014_auto_20170419_1339"),
        ("candidatos", "0004_auto_20170419_1339"),
    ]

    operations = [
        migrations.RemoveField(model_name="candidato", name="candidato_ps",),
        migrations.DeleteModel(name="Candidato",),
        migrations.CreateModel(
            name="Candidato",
            fields=[],
            options={"ordering": ["nome"], "proxy": True, "indexes": [],},
            bases=("base.pessoafisica",),
        ),
    ]