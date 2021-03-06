# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-09-30 16:29
from __future__ import unicode_literals

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion
import psct.dbfields
import psct.models.inscricao
import base.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("base", "0003_pessoafisica"),
        ("editais", "0003_cronograma_inscricao"),
        ("cursos", "0014_auto_20160930_1629"),
        ("processoseletivo", "0004_auto_20160930_1629"),
    ]

    operations = [
        migrations.CreateModel(
            name="Candidato",
            fields=[
                (
                    "pessoafisica_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="base.PessoaFisica",
                    ),
                ),
            ],
            options={
                "verbose_name": "Candidato do PSCT",
                "verbose_name_plural": "Candidatos do PSCT",
                "permissions": (
                    (
                        "admin_can_change_email",
                        "Administrador pode mudar email de candidato",
                    ),
                    ("list_candidato", "Administrador pode listar candidatos"),
                    (
                        "recover_candidato",
                        "Administrador pode recuperar dados de candidato",
                    ),
                ),
            },
            bases=("base.pessoafisica",),
        ),
        migrations.CreateModel(
            name="Comprovante",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nome",
                    models.CharField(
                        max_length=255, verbose_name="Nome ou descrição do Arquivo"
                    ),
                ),
                (
                    "arquivo",
                    psct.dbfields.DocumentFileField(
                        help_text="Somente arquivo pdf, png, jpg, jpeg ou tiff com até 5 MB.",
                        max_length=255,
                        upload_to=psct.models.inscricao.get_comprovantes_directory,
                        validators=[
                            base.validators.FileValidator(
                                allowed_extensions=[
                                    "pdf",
                                    "png",
                                    "jpg",
                                    "jpeg",
                                    "tiff",
                                ],
                                max_size=10485760,
                            )
                        ],
                        verbose_name="Arquivo",
                    ),
                ),
                (
                    "data_criacao",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data de criação"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data de atualização"
                    ),
                ),
            ],
            options={
                "verbose_name": "Comprovante",
                "verbose_name_plural": "Comprovantes",
            },
        ),
        migrations.CreateModel(
            name="CriterioAlternativa",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "posicao",
                    models.PositiveSmallIntegerField(
                        verbose_name="Posição da alternativa na questão"
                    ),
                ),
                ("descricao_alternativa", models.TextField(verbose_name="Alternativa")),
            ],
            options={
                "verbose_name": "Alternativa",
                "verbose_name_plural": "Alternativas",
                "ordering": ("posicao",),
            },
        ),
        migrations.CreateModel(
            name="CriterioQuestionario",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "numero",
                    models.PositiveSmallIntegerField(verbose_name="Número da questão"),
                ),
                (
                    "descricao_questao",
                    models.TextField(verbose_name="Descrição do Critério/Questão"),
                ),
                (
                    "multipla_escolha",
                    models.BooleanField(
                        default=False, verbose_name="Permite múltipla escolha"
                    ),
                ),
            ],
            options={
                "verbose_name": "Critério de Questionário",
                "verbose_name_plural": "Critérios de Questionário",
                "ordering": ("numero",),
            },
        ),
        migrations.CreateModel(
            name="Inscricao",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "aceite",
                    models.BooleanField(
                        default=False,
                        verbose_name="DECLARO, para os fins de direito, sob as penas da lei, que as informações que apresento para a inscrição\nsão fiéis à verdade e condizentes com a realidade dos fatos. Fico ciente, portanto, que a falsidade desta\ndeclaração configura-se em crime previsto no Código Penal Brasileiro e passível de apuração na forma da Lei.",
                    ),
                ),
                (
                    "data_criacao",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data de criação"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data de atualização"
                    ),
                ),
                (
                    "candidato",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="psct.Candidato",
                        verbose_name="Candidato",
                    ),
                ),
                (
                    "curso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="cursos.CursoNoCampus",
                        verbose_name="Curso",
                    ),
                ),
                (
                    "edital",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="editais.Edital",
                        verbose_name="Edital",
                    ),
                ),
            ],
            options={
                "verbose_name": "Inscrição",
                "verbose_name_plural": "Inscrições",
                "permissions": (
                    (
                        "recover_inscricao",
                        "Administrador pode recuperar dados de inscrição",
                    ),
                ),
            },
        ),
        migrations.CreateModel(
            name="Modalidade",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "texto",
                    models.TextField(
                        help_text="Texto que será exibido para o candidato",
                        verbose_name="Texto",
                    ),
                ),
                (
                    "equivalente",
                    models.OneToOneField(
                        help_text="Selecione a equivalência da modalidade que está sendo editada",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="equivalencia_psct",
                        to="processoseletivo.Modalidade",
                        verbose_name="Modalidade equivalente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Modalidade de cota",
                "verbose_name_plural": "Modalidades de cota",
                "ordering": ("equivalente",),
            },
        ),
        migrations.CreateModel(
            name="ModeloQuestionario",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nome",
                    models.CharField(
                        max_length=255,
                        unique=True,
                        verbose_name="Descrição do Modelo de Questionário",
                    ),
                ),
                (
                    "edital",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="editais.Edital",
                        verbose_name="edital",
                    ),
                ),
                (
                    "itens_avaliados",
                    models.ManyToManyField(
                        to="psct.CriterioQuestionario",
                        verbose_name="Critérios do questionário",
                    ),
                ),
            ],
            options={
                "verbose_name": "Modelo de Questionário",
                "verbose_name_plural": "Modelos de Questionários",
            },
        ),
        migrations.CreateModel(
            name="NotaAnual",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "ano",
                    models.PositiveSmallIntegerField(
                        choices=[(0, 0), (6, 6), (7, 7), (8, 8), (1, 1), (2, 2)],
                        verbose_name="Ano",
                    ),
                ),
                (
                    "portugues",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Português",
                    ),
                ),
                (
                    "matematica",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Matemática",
                    ),
                ),
                (
                    "historia",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="História",
                    ),
                ),
                (
                    "geografia",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Geografia",
                    ),
                ),
                (
                    "data_criacao",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data de criação"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data de atualização"
                    ),
                ),
            ],
            options={
                "verbose_name": "Nota Anual",
                "verbose_name_plural": "Notas Anuais",
                "ordering": ("ano",),
            },
        ),
        migrations.CreateModel(
            name="PontuacaoInscricao",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "valor",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Valor",
                    ),
                ),
                (
                    "valor_pt",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Valor de desempate PT",
                    ),
                ),
                (
                    "valor_mt",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("0.0"),
                        max_digits=5,
                        verbose_name="Valor de desempate MT",
                    ),
                ),
                (
                    "ensino_regular",
                    models.BooleanField(
                        default=True, verbose_name="Candidato cursou o ensino regular?"
                    ),
                ),
                (
                    "data_criacao",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data de criação"
                    ),
                ),
                (
                    "data_atualizacao",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Data de atualização"
                    ),
                ),
                (
                    "inscricao",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pontuacao",
                        to="psct.Inscricao",
                        verbose_name="Inscrição",
                    ),
                ),
            ],
            options={
                "verbose_name": "Pontuação da Inscrição",
                "verbose_name_plural": "Pontuações de Inscrição",
            },
        ),
        migrations.CreateModel(
            name="ProcessoInscricao",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "formacao",
                    models.CharField(
                        choices=[
                            ("INTEGRADO", "Técnico Integrado"),
                            ("SUBSEQUENTE", "Técnico Subsequente"),
                        ],
                        max_length=20,
                        verbose_name="Formação",
                    ),
                ),
                (
                    "data_inicio",
                    models.DateField(
                        verbose_name="Data de início do período de inscrição"
                    ),
                ),
                (
                    "data_encerramento",
                    models.DateField(
                        verbose_name="Data de encerramento do período de inscrição"
                    ),
                ),
                (
                    "cursos",
                    models.ManyToManyField(
                        to="cursos.CursoNoCampus", verbose_name="Cursos"
                    ),
                ),
                (
                    "edital",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="processo_inscricao",
                        to="editais.Edital",
                        verbose_name="Edital",
                    ),
                ),
            ],
            options={
                "verbose_name": "Processo de Inscrição do Edital",
                "verbose_name_plural": "Processos de Inscrição dos Editais",
                "ordering": ("edital",),
            },
        ),
        migrations.CreateModel(
            name="RespostaCriterio",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "criterio_alternativa_selecionada",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="psct.CriterioAlternativa",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RespostaModelo",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "candidato",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="psct.Candidato",
                        verbose_name="candidato",
                    ),
                ),
                (
                    "modelo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="psct.ModeloQuestionario",
                        verbose_name="modelo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Questionário Respondido",
                "verbose_name_plural": "Questionários Respondidos",
            },
        ),
        migrations.AddField(
            model_name="respostacriterio",
            name="resposta_modelo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="psct.RespostaModelo",
                verbose_name="Resposta do Modelo",
            ),
        ),
        migrations.AddField(
            model_name="notaanual",
            name="pontuacao",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="notas",
                to="psct.PontuacaoInscricao",
                verbose_name="Pontuação da Inscrição",
            ),
        ),
        migrations.AddField(
            model_name="inscricao",
            name="modalidade_cota",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="inscricoes_psct",
                to="psct.Modalidade",
                verbose_name="Modalidade da Cota",
            ),
        ),
        migrations.AddField(
            model_name="criterioalternativa",
            name="criterio",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="psct.CriterioQuestionario",
            ),
        ),
        migrations.AddField(
            model_name="comprovante",
            name="inscricao",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="comprovantes",
                to="psct.Inscricao",
                verbose_name="Inscrição",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="inscricao", unique_together=set([("candidato", "edital")]),
        ),
    ]
