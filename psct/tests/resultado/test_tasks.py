import datetime
from unittest import mock

from django.test import TestCase
from model_mommy import recipe

import base.tests.recipes
from psct import models, tasks
from psct.tests import mixins, recipes


class GerarResultadoPreliminarTestCase(
    mixins.EditalTestData,
    mixins.ModalidadeAmplaConcorrenciaSetUpTestData,
    mixins.CursoTestData,
    TestCase
):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.processoinscricao = recipes.processo_inscricao.make(
            edital=cls.edital,
            cursos=[cls.curso]
        )
        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            cls.fase_analise = recipes.fase_analise.make(edital=cls.edital)

        cls.inscricoes = recipes.inscricao.make(
            candidato=recipes.candidato.make,
            curso=cls.curso,
            edital=cls.edital,
            modalidade_cota=cls.modalidade_ampla,
            _quantity=3,
        )

        cls.pre_analises = []
        for inscricao in cls.inscricoes:
            cls.pre_analises.append(
                recipes.inscricao_pre_analise.make(
                    candidato=inscricao.candidato,
                    fase=cls.fase_analise,
                    curso=cls.curso,
                    modalidade=cls.modalidade_ampla,
                    situacao=models.SituacaoInscricao.DEFERIDA.name,
                )
            )

        cls.pre_analise_indeferida = recipes.inscricao_pre_analise.make(
            candidato=recipes.candidato.make,
            fase=cls.fase_analise,
            curso=cls.curso,
            modalidade=cls.modalidade_ampla,
            situacao=models.SituacaoInscricao.INDEFERIDA.name
        )
        cls.inscricao_indeferida = recipes.inscricao.make(
            curso=cls.curso,
            edital=cls.edital,
            candidato=cls.pre_analise_indeferida.candidato,
            modalidade_cota=cls.modalidade_ampla,
        )
        with mock.patch("psct.export.export") as export:
            cls.export = export
            tasks.resultado.gerar_resultado_preliminar(cls.fase_analise.pk)

    def test_deve_exportar_o_resultado(self):
        resultado = models.ResultadoPreliminar.objects.get(fase=self.fase_analise)
        self.export.assert_called_with(resultado)

    def test_deve_gerar_resultado_preliminar_para_a_fase(self):
        self.assertTrue(models.ResultadoPreliminar.objects.filter(fase=self.fase_analise).exists())

    def test_deve_gerar_resultado_preliminar_para_curso(self):
        resultado = models.ResultadoPreliminar.objects.get(fase=self.fase_analise)
        self.assertTrue(
            models.ResultadoPreliminarCurso.objects.filter(
                resultado=resultado, curso=self.curso
            ).exists(),
        )

    def test_deve_gerar_resultado_preliminar_para_inscricoes_deferidas(self):
        resultados_inscricoes = models.ResultadoPreliminarInscricao.objects.values_list(
            "inscricao", flat=True
        )
        for inscricao in self.inscricoes:
            self.assertIn(
                inscricao.id,
                resultados_inscricoes
            )

    def test_deve_gerar_resultado_preliminar_para_inscricao_indeferida(self):
        resultado = models.ResultadoPreliminarInscricaoIndeferida.objects.first()
        self.assertEqual(self.inscricao_indeferida.id, resultado.inscricao.id)

    def test_deve_gerar_classificacao_cota(self):
        resultados_inscricoes = models.ResultadoPreliminarInscricao.objects.all()
        for resultado in resultados_inscricoes:
            self.assertIsNotNone(resultado.classificacao_cota)

    def test_deve_gerar_classificacao(self):
        resultados_inscricoes = models.ResultadoPreliminarInscricao.objects.all()
        for resultado in resultados_inscricoes:
            self.assertIsNotNone(resultado.classificacao)


class GerarResultadoPreliminarClassificacaoTestCase(
    mixins.EditalTestData,
    mixins.ModalidadeAmplaConcorrenciaSetUpTestData,
    mixins.CursoTestData,
    TestCase
):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.processoinscricao = recipes.processo_inscricao.make(
            edital=cls.edital,
            cursos=[cls.curso]
        )
        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            cls.fase_analise = recipes.fase_analise.make(edital=cls.edital)

        cls.inscricoes = recipes.inscricao.make(
            candidato=recipes.candidato.make,
            curso=cls.curso,
            edital=cls.edital,
            modalidade_cota=cls.modalidade_ampla,
            _quantity=3,
        )

    def test_deve_gerar_classificacao_considerando_pontuacao_como_primeiro_criterio(self):
        pre_analises = []
        pontuacao_seq = recipe.seq(8.0, increment_by=-1.0)
        for inscricao in self.inscricoes:
            pre_analises.append(
                recipes.inscricao_pre_analise.make(
                    candidato=inscricao.candidato,
                    fase=self.fase_analise,
                    curso=self.curso,
                    modalidade=self.modalidade_ampla,
                    situacao=models.SituacaoInscricao.DEFERIDA.name,
                    pontuacao=next(pontuacao_seq),
                )
            )

        with mock.patch("psct.export.export"):
            tasks.resultado.gerar_resultado_preliminar(self.fase_analise.pk)

        resultados_inscricoes = models.ResultadoPreliminarInscricao.objects.all()
        self.assertEqual(
            pre_analises,
            [resultado.inscricao_preanalise for resultado in resultados_inscricoes]
        )

    def test_deve_gerar_classificacao_considerando_pontuacao_pt_como_segundo_criterio(self):
        pre_analises = []
        pontuacao = 5.0
        pontuacao_pt_seq = recipe.seq(8.0, increment_by=-1.0)
        for inscricao in self.inscricoes:
            pre_analises.append(
                recipes.inscricao_pre_analise.make(
                    candidato=inscricao.candidato,
                    fase=self.fase_analise,
                    curso=self.curso,
                    modalidade=self.modalidade_ampla,
                    situacao=models.SituacaoInscricao.DEFERIDA.name,
                    pontuacao=pontuacao,
                    pontuacao_pt=next(pontuacao_pt_seq),
                )
            )

        with mock.patch("psct.export.export"):
            tasks.resultado.gerar_resultado_preliminar(self.fase_analise.pk)

        resultados_inscricoes = models.ResultadoPreliminarInscricao.objects.all()
        self.assertEqual(
            pre_analises,
            [resultado.inscricao_preanalise for resultado in resultados_inscricoes]
        )

    def test_deve_gerar_classificacao_considerando_pontuacao_mt_como_terceiro_criterio(self):
        pre_analises = []
        pontuacao = 5.0
        pontuacao_pt = 5.0
        pontuacao_mt_seq = recipe.seq(8.0, increment_by=-1.0)
        for inscricao in self.inscricoes:
            pre_analises.append(
                recipes.inscricao_pre_analise.make(
                    candidato=inscricao.candidato,
                    fase=self.fase_analise,
                    curso=self.curso,
                    modalidade=self.modalidade_ampla,
                    situacao=models.SituacaoInscricao.DEFERIDA.name,
                    pontuacao=pontuacao,
                    pontuacao_pt=pontuacao_pt,
                    pontuacao_mt=next(pontuacao_mt_seq),
                )
            )

        with mock.patch("psct.export.export"):
            tasks.resultado.gerar_resultado_preliminar(self.fase_analise.pk)

        resultados_inscricoes = models.ResultadoPreliminarInscricao.objects.all()
        self.assertEqual(
            pre_analises,
            [resultado.inscricao_preanalise for resultado in resultados_inscricoes]
        )

    def test_deve_gerar_classificacao_considerando_nascimento_como_quarto_criterio(self):
        pre_analises = []
        pontuacao = 5.0
        pontuacao_pt = 5.0
        pontuacao_mt = 5.0
        nascimento_seq = recipe.seq(datetime.date.today(), increment_by=datetime.timedelta(days=1))
        for inscricao in self.inscricoes:
            pre_analises.append(
                recipes.inscricao_pre_analise.make(
                    candidato=inscricao.candidato,
                    fase=self.fase_analise,
                    curso=self.curso,
                    modalidade=self.modalidade_ampla,
                    situacao=models.SituacaoInscricao.DEFERIDA.name,
                    pontuacao=pontuacao,
                    pontuacao_pt=pontuacao_pt,
                    pontuacao_mt=pontuacao_mt,
                    nascimento=next(nascimento_seq)
                )
            )

        with mock.patch("psct.export.export"):
            tasks.resultado.gerar_resultado_preliminar(self.fase_analise.pk)

        resultados_inscricoes = models.ResultadoPreliminarInscricao.objects.all()
        self.assertEqual(
            pre_analises,
            [resultado.inscricao_preanalise for resultado in resultados_inscricoes]
        )


class ExportarResultadoArquivoTestCase(TestCase):

    @mock.patch("psct.tasks.resultado.driver.Driver.run")
    @mock.patch("psct.tasks.resultado.driver.Driver.report")
    @mock.patch("psct.tasks.resultado.driver.get_driver")
    def test_deveria_retornar_o_report_do_driver(self, get_driver, report, run):
        get_driver.return_value.return_value.run = run
        get_driver.return_value.return_value.report = report
        user = base.tests.recipes.user.make()
        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            resultado = recipes.resultado_preliminar.make()
        render_id = mock.Mock()
        filetype = mock.Mock()
        tasks.resultado.exportar_resultado_arquivo(user.id, resultado.id, render_id, filetype)
        run.assert_called()
        report.assert_called()
