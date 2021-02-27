# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-27 12:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0006_pessoafisica_nome_social"),
    ]

    operations = [
        migrations.AddField(
            model_name="pessoafisica",
            name="certidao_data",
            field=models.DateField(
                blank=True, null=True, verbose_name="Data de Emissão da Certidão Civil"
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="certidao_folha",
            field=models.CharField(
                blank=True,
                max_length=30,
                null=True,
                verbose_name="Folha da Certidão Civil",
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="certidao_livro",
            field=models.CharField(
                blank=True,
                max_length=30,
                null=True,
                verbose_name="Livro da Certidão Civil",
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="certidao_tipo",
            field=models.CharField(
                blank=True,
                choices=[("NASCIMENTO", "Nascimento"), ("CASAMENTO", "Casamento")],
                max_length=10,
                null=True,
                verbose_name="Tipo de Certidão Civil",
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="data_emissao_titulo_eleitor",
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name="Data de Emissão do Título de Eleitor",
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="email_responsavel",
            field=models.EmailField(
                blank=True,
                max_length=100,
                null=True,
                verbose_name="E-mail do Responsável",
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="nacionalidade_old",
            field=models.CharField(
                blank=True, max_length=55, verbose_name="Nacionalidade (Antigo)"
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="nome_pai",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Nome do Pai"
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="nome_responsavel",
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
                verbose_name="Nome do Responsável",
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="numero_titulo_eleitor",
            field=models.CharField(
                blank=True,
                max_length=30,
                null=True,
                verbose_name="Número do Título de Eleitor",
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="orgao_expeditor_uf",
            field=models.CharField(
                blank=True,
                choices=[
                    ("AC", "Acre"),
                    ("AL", "Alagoas"),
                    ("AP", "Amapa"),
                    ("AM", "Amazonas"),
                    ("BA", "Bahia"),
                    ("CE", "Ceará"),
                    ("DF", "Distrito Federal"),
                    ("ES", "Espírito Santo"),
                    ("GO", "Goiás"),
                    ("MA", "Maranhão"),
                    ("MT", "Mato Grosso"),
                    ("MS", "Mato Grosso do Sul"),
                    ("MG", "Minas Gerais"),
                    ("PA", "Pará"),
                    ("PB", "Paraíba"),
                    ("PR", "Paraná"),
                    ("PE", "Pernambuco"),
                    ("PI", "Piauí"),
                    ("RJ", "Rio de Janeiro"),
                    ("RN", "Rio Grande do Norte"),
                    ("RS", "Rio Grande do Sul"),
                    ("RO", "Rondônia"),
                    ("RR", "Roraima"),
                    ("SC", "Santa Catarina"),
                    ("SP", "São Paulo"),
                    ("SE", "Sergipe"),
                    ("TO", "Tocantis"),
                ],
                max_length=2,
                null=True,
                verbose_name="Estado Emissor do RG",
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="parentesco_responsavel",
            field=models.CharField(
                blank=True,
                choices=[
                    ("PAIS", "Pai/Mãe"),
                    ("AVOS", "Avô/Avó"),
                    ("TIOS", "Tio/Tia"),
                    ("SOBRINHOS", "Sobrinho/Sobrinha"),
                    ("OUTROS", "Outro"),
                ],
                max_length=10,
                null=True,
                verbose_name="Parentesco do Responsável",
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="secao_titulo_eleitor",
            field=models.CharField(
                blank=True,
                max_length=10,
                null=True,
                verbose_name="Seção do Título de Eleitor",
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="tipo_zona_residencial",
            field=models.CharField(
                blank=True,
                choices=[("URBANA", "Urbana"), ("RURAL", "Rural")],
                max_length=15,
                null=True,
                verbose_name="Zona Residencial",
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="uf_titulo_eleitor",
            field=models.CharField(
                blank=True,
                choices=[
                    ("AC", "Acre"),
                    ("AL", "Alagoas"),
                    ("AP", "Amapa"),
                    ("AM", "Amazonas"),
                    ("BA", "Bahia"),
                    ("CE", "Ceará"),
                    ("DF", "Distrito Federal"),
                    ("ES", "Espírito Santo"),
                    ("GO", "Goiás"),
                    ("MA", "Maranhão"),
                    ("MT", "Mato Grosso"),
                    ("MS", "Mato Grosso do Sul"),
                    ("MG", "Minas Gerais"),
                    ("PA", "Pará"),
                    ("PB", "Paraíba"),
                    ("PR", "Paraná"),
                    ("PE", "Pernambuco"),
                    ("PI", "Piauí"),
                    ("RJ", "Rio de Janeiro"),
                    ("RN", "Rio Grande do Norte"),
                    ("RS", "Rio Grande do Sul"),
                    ("RO", "Rondônia"),
                    ("RR", "Roraima"),
                    ("SC", "Santa Catarina"),
                    ("SP", "São Paulo"),
                    ("SE", "Sergipe"),
                    ("TO", "Tocantis"),
                ],
                max_length=10,
                null=True,
                verbose_name="Estado Emissor do Título de Eleitor",
            ),
        ),
        migrations.AddField(
            model_name="pessoafisica",
            name="zona_titulo_eleitor",
            field=models.CharField(
                blank=True,
                max_length=10,
                null=True,
                verbose_name="Zona do Título de Eleitor",
            ),
        ),
        migrations.AlterField(
            model_name="pessoafisica",
            name="certidao",
            field=models.CharField(
                blank=True,
                max_length=30,
                null=True,
                verbose_name="Número do Termo da Certidão Civil",
            ),
        ),
        migrations.AlterField(
            model_name="pessoafisica",
            name="data_expedicao",
            field=models.DateField(
                blank=True, null=True, verbose_name="Data de Emissão do RG"
            ),
        ),
        migrations.AlterField(
            model_name="pessoafisica",
            name="nacionalidade",
            field=models.CharField(
                choices=[("BRASILEIRA", "Brasileira"), ("ESTRANGEIRA", "Estrangeira")],
                max_length=55,
                verbose_name="Nacionalidade",
            ),
        ),
        migrations.AlterField(
            model_name="pessoafisica",
            name="naturalidade",
            field=models.CharField(
                blank=True, max_length=55, null=True, verbose_name="Naturalidade"
            ),
        ),
        migrations.AlterField(
            model_name="pessoafisica",
            name="naturalidade_uf",
            field=models.CharField(
                blank=True,
                choices=[
                    ("AC", "Acre"),
                    ("AL", "Alagoas"),
                    ("AP", "Amapa"),
                    ("AM", "Amazonas"),
                    ("BA", "Bahia"),
                    ("CE", "Ceará"),
                    ("DF", "Distrito Federal"),
                    ("ES", "Espírito Santo"),
                    ("GO", "Goiás"),
                    ("MA", "Maranhão"),
                    ("MT", "Mato Grosso"),
                    ("MS", "Mato Grosso do Sul"),
                    ("MG", "Minas Gerais"),
                    ("PA", "Pará"),
                    ("PB", "Paraíba"),
                    ("PR", "Paraná"),
                    ("PE", "Pernambuco"),
                    ("PI", "Piauí"),
                    ("RJ", "Rio de Janeiro"),
                    ("RN", "Rio Grande do Norte"),
                    ("RS", "Rio Grande do Sul"),
                    ("RO", "Rondônia"),
                    ("RR", "Roraima"),
                    ("SC", "Santa Catarina"),
                    ("SP", "São Paulo"),
                    ("SE", "Sergipe"),
                    ("TO", "Tocantis"),
                ],
                max_length=2,
                null=True,
                verbose_name="UF da Naturalidade",
            ),
        ),
        migrations.AlterField(
            model_name="pessoafisica",
            name="nome_mae",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Nome da Mãe"
            ),
        ),
        migrations.AlterField(
            model_name="pessoafisica",
            name="orgao_expeditor",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="Orgão Emissor do RG"
            ),
        ),
        migrations.AlterField(
            model_name="pessoafisica",
            name="rg",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="Número do RG"
            ),
        ),
    ]