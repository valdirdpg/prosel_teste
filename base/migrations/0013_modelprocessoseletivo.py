# Generated by Django 2.2.14 on 2021-02-05 16:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('processoseletivo', '0029_edicao_descricao'),
        ('base', '0012_merge_20210119_1440'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelProcessoseletivo',
            fields=[
                ('processoseletivo_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='processoseletivo.ProcessoSeletivo')),
            ],
            bases=('processoseletivo.processoseletivo',),
        ),
    ]