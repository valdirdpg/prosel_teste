# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-09-30 16:29
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cursos", "0013_auto_20160821_1230"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="campus",
            options={"ordering": ("nome",), "verbose_name_plural": "Campi"},
        ),
    ]
