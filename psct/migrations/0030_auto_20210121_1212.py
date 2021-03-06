# Generated by Django 2.2.14 on 2021-01-21 12:12

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('psct', '0029_auto_20210121_1140'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notaanual',
            name='ciencias_natureza',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.0'), max_digits=5, verbose_name='Ciências da natureza'),
        ),
        migrations.AlterField(
            model_name='pontuacaoinscricao',
            name='valor',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.0'), max_digits=5, verbose_name='Valor'),
        ),
        migrations.AlterField(
            model_name='pontuacaoinscricao',
            name='valor_mt',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.0'), max_digits=5, verbose_name='Valor de desempate MT'),
        ),
        migrations.AlterField(
            model_name='pontuacaoinscricao',
            name='valor_pt',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.0'), max_digits=5, verbose_name='Valor de desempate PT'),
        ),
        migrations.AlterField(
            model_name='pontuacaoinscricao',
            name='valor_redacao',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.0'), max_digits=5, verbose_name='Valor de desempate - Redação'),
        ),
    ]
