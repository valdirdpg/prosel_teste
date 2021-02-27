# Generated by Django 2.2.3 on 2019-07-09 16:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("psct", "0019_update_cpf_recurso"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="consulta",
            options={
                "ordering": ("nome",),
                "verbose_name": "Consulta",
                "verbose_name_plural": "Consultas",
            },
        ),
        migrations.AlterModelOptions(
            name="inscricao",
            options={
                "permissions": (
                    (
                        "recover_inscricao",
                        "Administrador pode recuperar dados de inscrição",
                    ),
                    ("list_inscricao", "Administrador pode listar inscrições"),
                    (
                        "add_list_inscritos",
                        "Administrador pode criar listar de inscrições",
                    ),
                ),
                "verbose_name": "Inscrição",
                "verbose_name_plural": "Inscrições",
            },
        ),
        migrations.AlterField(
            model_name="processoinscricao",
            name="cursos",
            field=models.ManyToManyField(
                limit_choices_to={"excluido": False},
                to="cursos.CursoNoCampus",
                verbose_name="Cursos",
            ),
        ),
    ]
