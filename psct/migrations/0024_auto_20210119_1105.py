# Generated by Django 2.2.14 on 2021-01-19 11:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('psct', '0023_auto_20210118_1813'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inscricao',
            name='marcou_baixa_renda',
        ),
        migrations.RemoveField(
            model_name='inscricao',
            name='marcou_escola_publica',
        ),
        migrations.RemoveField(
            model_name='inscricao',
            name='marcou_pcd',
        ),
        migrations.RemoveField(
            model_name='inscricao',
            name='marcou_ppi',
        ),
    ]
