# Generated by Django 2.2.14 on 2021-01-18 22:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0028_curso_selecao'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cidade',
            name='uf',
            field=models.CharField(choices=[('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapa'), ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'), ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'), ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantis'), ('ON', 'Outra Nacionalidade')], max_length=2, verbose_name='UF'),
        ),
        migrations.AlterField(
            model_name='cursonocampus',
            name='formacao',
            field=models.CharField(choices=[('INTEGRADO', 'Técnico Integrado'), ('SUBSEQUENTE', 'Técnico Subsequente'), ('TECNOLOGICO', 'Tecnológico'), ('BACHARELADO', 'Bacharelado'), ('LICENCIATURA', 'Licenciatura'), ('ESPECIALIZACAO', 'Especialização'), ('MESTRADO', 'Mestrado'), ('DOUTORADO', 'Doutorado'), ('CONCOMITANTE', 'Concomitante')], max_length=16, verbose_name='Formação'),
        ),
        migrations.AlterField(
            model_name='cursonocampus',
            name='turno',
            field=models.CharField(choices=[('MATUTINO', 'Matutino'), ('VESPERTINO', 'Vespertino'), ('NOTURNO', 'Noturno'), ('INTEGRAL', 'Integral'), ('DIURNO', 'Diurno'), ('PREDOMINANTEMENTE_MATUTINO', 'Predominantemente Matutino'), ('PREDOMINANTEMENTE_VESPERTINO', 'Predominantemente Vespertino'), ('NOTURNO_EVEN_AULAS_SABADO', 'Noturno + Eventuais Aulas Sabado'), ('NOTURNO_SABADO_VESPERTINO', 'Noturno + Sabado Vespertino')], max_length=10),
        ),
        migrations.AlterField(
            model_name='ies',
            name='uf',
            field=models.CharField(choices=[('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapa'), ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'), ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'), ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantis'), ('ON', 'Outra Nacionalidade')], max_length=2, verbose_name='UF'),
        ),
    ]
