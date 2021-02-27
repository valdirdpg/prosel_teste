# Generated by Django 2.2.14 on 2020-12-02 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidatos', '0009_auto_20190523_1001'),
    ]

    operations = [
        migrations.AlterField(
            model_name='caracterizacao',
            name='declara_veracidade',
            field=models.BooleanField(verbose_name='DECLARO, para os fins de direito, sob as penas da lei, que as informações e os documentos que apresento para pré-matrícula no IFBA, são fiéis à verdade e condizentes com a realidade dos fatos. Fico ciente, portanto, que a falsidade desta declaração configura-se em crime previsto no Código Penal Brasileiro e passível de apuração na forma da Lei.'),
        ),
    ]
