from unittest import mock

from django.test import TestCase

from base.tests.mixins import UserTestMixin
from cursos.tests.mixins import DiretorEnsinoPermissionData
from . import recipes
from .. import models
from .. import pdf
from ..choices import Status


class RelatorioFinalEtapaTestCase(DiretorEnsinoPermissionData, UserTestMixin, TestCase):
    def test_status_deveria_estar_configurado_corretamente(self):
        self.assertIsNone(pdf.RelatorioFinalEtapa.status)

    def test_title_deveria_estar_configurado_corretamente(self):
        self.assertEqual("", pdf.RelatorioFinalEtapa.title)

    def test_prefix_deveria_estar_configurado_corretamente(self):
        self.assertEqual("resultado_final", pdf.RelatorioFinalEtapa.prefix)

    def test_ordering_lista_deveria_estar_configurado_corretamente(self):
        self.assertIsNone(pdf.RelatorioFinalEtapa.ordering_lista)

    def test_ordering_msg_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            "Listagem em ordem de classificação por Curso, Turno e Modalidade.",
            pdf.RelatorioFinalEtapa.ordering_msg,
        )

    def test_get_table_deveria_lancar_excecao(self):
        etapa = recipes.etapa.make()
        chamada = recipes.chamada.make(etapa=etapa)
        with self.assertRaises(NotImplementedError) as ex:
            pdf.RelatorioFinalEtapa(etapa, self.usuario_base).get_table(chamada)

        self.assertEqual(
            "É necessário implementar o método get_table com a tabela a ser gerada.",
            ex.exception.args[0],
        )

    def test_has_output_deveria_retornar_falso(self):
        etapa = recipes.etapa.make()
        chamada = recipes.chamada.make(etapa=etapa)
        self.assertFalse(
            pdf.RelatorioFinalEtapa(etapa, self.usuario_base).has_output(chamada)
        )

    @mock.patch(
        "processoseletivo.pdf.RelatorioFinalEtapa.status",
        new_callable=mock.PropertyMock,
    )
    def test_has_output_deveria_retornar_verdadeiro(self, status):
        status.return_value = "DEFERIDO"
        etapa = recipes.etapa.make()
        chamada = recipes.chamada.make(etapa=etapa)
        inscricao = recipes.inscricao.make(chamada=chamada)
        recipes.resultado.make(etapa=etapa, inscricao=inscricao)
        self.assertTrue(
            pdf.RelatorioFinalEtapa(etapa, self.usuario_base).has_output(chamada)
        )


class RelatorioFinalDeferidosTestCase(TestCase):
    def test_status_deveria_estar_configurado_corretamente(self):
        self.assertEqual("DEFERIDO", pdf.RelatorioFinalDeferidos.status)

    def test_title_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            "Lista de Candidatos Deferidos", pdf.RelatorioFinalDeferidos.title
        )

    def test_prefix_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            "resultado_final_deferidos", pdf.RelatorioFinalDeferidos.prefix
        )

    def test_ordering_lista_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            ["inscricao__desempenho__classificacao"],
            pdf.RelatorioFinalDeferidos.ordering_lista,
        )

    def test_ordering_msg_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            "Listagem em ordem de classificação por Curso, Turno e Modalidade.",
            pdf.RelatorioFinalDeferidos.ordering_msg,
        )


class RelatorioFinalIndeferidosTestCase(TestCase):
    def test_status_deveria_estar_configurado_corretamente(self):
        self.assertEqual("INDEFERIDO", pdf.RelatorioFinalIndeferidos.status)

    def test_title_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            "Lista de Candidatos Indeferidos", pdf.RelatorioFinalIndeferidos.title
        )

    def test_prefix_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            "resultado_final_indeferidos", pdf.RelatorioFinalIndeferidos.prefix
        )

    def test_ordering_lista_deveria_estar_configurado_corretamente(self):
        self.assertIsNone(pdf.RelatorioFinalIndeferidos.ordering_lista)

    def test_ordering_msg_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            "Listagem em ordem de classificação por Curso, Turno e Modalidade.",
            pdf.RelatorioFinalIndeferidos.ordering_msg,
        )


class RelatorioFinalExcedentesTestCase(TestCase):
    def test_status_deveria_estar_configurado_corretamente(self):
        self.assertEqual("EXCEDENTE", pdf.RelatorioFinalExcedentes.status)

    def test_title_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            "Lista de Candidatos Excedentes", pdf.RelatorioFinalExcedentes.title
        )

    def test_prefix_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            "resultado_final_excedentes", pdf.RelatorioFinalExcedentes.prefix
        )

    def test_ordering_lista_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            ["inscricao__desempenho__classificacao"],
            pdf.RelatorioFinalExcedentes.ordering_lista,
        )

    def test_ordering_msg_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            "Listagem em ordem de classificação por Curso, Turno e Modalidade.",
            pdf.RelatorioFinalExcedentes.ordering_msg,
        )


class RelatorioConvocadosPorCotaTestCase(
    DiretorEnsinoPermissionData, UserTestMixin, TestCase
):
    def test_title_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            "Lista de Convocados por Cota", pdf.RelatorioConvocadosPorCota.title
        )

    def test_prefix_deveria_estar_configurado_corretamente(self):
        self.assertEqual("lista-convocados", pdf.RelatorioConvocadosPorCota.prefix)

    def test_ordering_lista_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            ["desempenho__classificacao"], pdf.RelatorioConvocadosPorCota.ordering_lista
        )

    def test_get_lista_deveria_retornar_nenhuma_inscricao(self):
        etapa = recipes.etapa.make()
        chamada = recipes.chamada.make(etapa=etapa)
        inscricoes = pdf.RelatorioConvocadosPorCota(etapa, self.usuario_base).get_lista(
            chamada
        )
        self.assertFalse(inscricoes.exists())

    def test_get_lista_deveria_retornar_inscricoes_em_ordem_classificacao(self):
        etapa = recipes.etapa.make()
        chamada = recipes.chamada.make(etapa=etapa)
        inscricao1 = recipes.inscricao.make(chamada=chamada)
        inscricao2 = recipes.inscricao.make(chamada=chamada)
        recipes.desempenho.make(inscricao=inscricao2, classificacao=1)
        recipes.desempenho.make(inscricao=inscricao1, classificacao=2)
        inscricoes = pdf.RelatorioConvocadosPorCota(etapa, self.usuario_base).get_lista(
            chamada
        )
        self.assertEqual(inscricoes[0], inscricao2)
        self.assertEqual(inscricoes[1], inscricao1)

    def test_has_output_deveria_falso(self):
        etapa = recipes.etapa.make()
        chamada = recipes.chamada.make(etapa=etapa)
        self.assertFalse(
            pdf.RelatorioConvocadosPorCota(etapa, self.usuario_base).has_output(chamada)
        )

    def test_has_output_deveria_verdadeiro(self):
        etapa = recipes.etapa.make()
        chamada = recipes.chamada.make(etapa=etapa)
        recipes.inscricao.make(chamada=chamada)
        self.assertTrue(
            pdf.RelatorioConvocadosPorCota(etapa, self.usuario_base).has_output(chamada)
        )


class VerificaDocumentoRecursoTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.etapa = recipes.etapa.make()
        cls.chamada = recipes.chamada.make(etapa=cls.etapa)
        cls.inscricao = recipes.inscricao.make(chamada=cls.chamada)

    def test_deveria_retornar_verificar(self):
        expected = "VERIFICAR", "VERIFICAR"
        self.assertEqual(
            expected,
            pdf.verificar_documento_e_recurso(self.inscricao, 10, 9, self.etapa),
        )

    @mock.patch("processoseletivo.pdf.verificar_status")
    def test_deveria_retornar_documentacao_nao_entregue(self, verificar_status):
        verificar_status.return_value = (
            Status.INDEFERIDO.value,
            "DOCUMENTAÇÃO NÃO ENTREGUE",
        )
        expected = "INDEFERIDO", "DOCUMENTAÇÃO NÃO ENTREGUE"
        self.assertEqual(
            expected,
            pdf.verificar_documento_e_recurso(self.inscricao, 9, 10, self.etapa),
        )


class CadastroResultadoPreliminar(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.inscricao = recipes.inscricao.make()

    def test_deveriar_criar_resultado(self):
        pdf.cadastrar_resultado_preliminar(
            self.inscricao,
            self.inscricao.chamada.etapa,
            Status.INDEFERIDO.name,
            "Observação",
        )
        self.assertTrue(
            models.Resultado.objects.filter(
                inscricao=self.inscricao,
                etapa=self.inscricao.chamada.etapa,
                status=Status.INDEFERIDO.name,
                observacao="Observação",
            ).exists()
        )

    def test_deveria_atualizar_resultado(self):
        recipes.resultado.make(
            inscricao=self.inscricao,
            etapa=self.inscricao.chamada.etapa,
            status=Status.INDEFERIDO.name,
            observacao="Observação",
        )
        pdf.cadastrar_resultado_preliminar(
            self.inscricao,
            self.inscricao.chamada.etapa,
            Status.DEFERIDO.name,
            "Nova observação",
        )
        self.assertTrue(
            models.Resultado.objects.filter(
                inscricao=self.inscricao,
                etapa=self.inscricao.chamada.etapa,
                status=Status.DEFERIDO.name,
                observacao="Nova observação",
            ).exists()
        )
