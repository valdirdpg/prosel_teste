# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-08-21 12:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("cursos", "0012_auto_20160821_1156"),
    ]

    operations = [
        migrations.AlterField(
            model_name="disciplina",
            name="nome",
            field=models.CharField(max_length=128, unique=True),
        ),
        migrations.RemoveField(model_name="cursoead", name="cursonocampus_ptr",),
        migrations.RemoveField(model_name="cursopresencial", name="cursonocampus_ptr",),
        migrations.RemoveField(model_name="vagasead", name="curso",),
        migrations.RemoveField(model_name="vagasead", name="polo",),
        migrations.AddField(
            model_name="cursonocampus",
            name="perfil",
            field=models.TextField(
                blank=True, null=True, verbose_name="Perfil Profissional"
            ),
        ),
        migrations.DeleteModel(name="CursoEAD",),
        migrations.DeleteModel(name="CursoPresencial",),
        migrations.DeleteModel(name="VagasEAD",),
        migrations.AlterField(
            model_name="vagacurso",
            name="vagas_s1",
            field=models.PositiveIntegerField(
                default=0, verbose_name="Vagas no 1º Semestre"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="vagacurso",
            name="vagas_s2",
            field=models.PositiveIntegerField(
                default=0, verbose_name="Vagas no 2º Semestre"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="disciplinacurso",
            name="ch",
            field=models.IntegerField(verbose_name="Carga Horária"),
        ),
        migrations.AlterField(
            model_name="disciplinacurso",
            name="periodo",
            field=models.IntegerField(verbose_name="Período ou Ano"),
        ),
        migrations.AddField(
            model_name="campus",
            name="diretor_ensino_substituto",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="campus_dir_ensino_subs",
                to="cursos.Docente",
                verbose_name="Diretor de Ensino Substituto",
            ),
        ),
        migrations.AlterField(
            model_name="campus",
            name="diretor_ensino",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="campus_dir_ensino",
                to="cursos.Docente",
                verbose_name="Diretor de Ensino",
            ),
        ),
    ]
