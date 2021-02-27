# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-01-10 09:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("candidatos", "0002_auto_20160321_1816"),
    ]

    operations = [
        migrations.AlterField(
            model_name="caracterizacao",
            name="candidato",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="base.PessoaFisica",
                verbose_name="Candidato",
            ),
        ),
        migrations.AlterField(
            model_name="caracterizacao",
            name="ensino_medio_conclusao",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="Ano de conclusão do Ensino Médio"
            ),
        ),
        migrations.AlterField(
            model_name="caracterizacao",
            name="escola_ensino_fundamental",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="candidatos.TipoEscola",
                verbose_name="Tipo de escola que cursou o Ensino Fundamental",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="caracterizacao",
            name="nome_escola_ensino_fundamental",
            field=models.CharField(
                default=1,
                max_length=50,
                verbose_name="Nome da escola que fez o Ensino Fundamental",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="caracterizacao",
            name="renda_bruta_familiar",
            field=models.DecimalField(
                decimal_places=2,
                help_text="Considerar a soma de todos os rendimentos mensais da família sem os descontos.",
                max_digits=8,
                verbose_name="Renda Bruta Familiar R$",
            ),
        ),
        migrations.AlterField(
            model_name="caracterizacao",
            name="tipo_area_escola_ensino_fundamental",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tipo_area_escola_ensino_fundamental",
                to="candidatos.TipoAreaResidencial",
                verbose_name="Tipo de localização da escola que fez o ensino fundamental",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="inscricaocaracterizacao",
            name="candidato",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="base.PessoaFisica",
                verbose_name="Candidato",
            ),
        ),
    ]