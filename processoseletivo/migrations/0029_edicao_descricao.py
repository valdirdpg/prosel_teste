# Generated by Django 2.2.14 on 2021-02-05 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processoseletivo', '0028_auto_20210127_1353'),
    ]

    operations = [
        migrations.AddField(
            model_name='edicao',
            name='descricao',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
