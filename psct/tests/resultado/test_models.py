from unittest import mock

from django.test import TestCase
from django.utils.formats import localize

import cursos.models
import cursos.recipes
from processoseletivo.models import ModalidadeEnum
from psct import models
from psct.tests import recipes


class ResultadoPreliminarTestCase(TestCase):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.campus_patcher = mock.patch.multiple(
            cursos.models.Campus,
            cria_usuarios_diretores=mock.DEFAULT,
            adiciona_permissao_diretores=mock.DEFAULT,
            remove_permissao_diretores=mock.DEFAULT
        )
        cls.fase_analise_patcher = mock.patch.multiple(
            models.FaseAnalise,
            atualizar_grupos_permissao=mock.DEFAULT,
        )
        cls.campus_patcher.start()
        cls.fase_analise_patcher.start()
        cls.processo_inscricao = recipes.processo_inscricao.make()
        cls.edital = cls.processo_inscricao.edital
        cls.curso = cursos.recipes.curso_selecao.make()
        cls.resultado = recipes.resultado_preliminar.make(fase__edital=cls.edital)
        cls.modalidade_ampla = models.Modalidade.objects.get(id=ModalidadeEnum.ampla_concorrencia)

    def test_str_deveria_estar_corretamente_configurado(self):
        date = localize(self.resultado.data_cadastro)
        self.assertEqual(
            f"Resultado Preliminar da {self.resultado.fase} de {date}",
            str(self.resultado)
        )

    def test_get_inscricoes_deveria_ser_vazio_quando_nao_ha_resultado_preliminar_inscricao(self):
        inscricoes = self.resultado.get_inscricoes(self.curso, self.modalidade_ampla)
        self.assertFalse(inscricoes.exists())

    def test_get_inscricoes_nao_deveria_aplicar_filtro_de_modalidade_para_ampla(self):
        recipes.vagas_resultado_preliminar.make(
            resultado_curso__resultado=self.resultado,
            resultado_curso__curso=self.curso,
            modalidade=self.modalidade_ampla,
            quantidade=2,
        )
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=self.modalidade_ampla
        )
        resultado_inscricao = recipes.resultado_preliminar_inscricao.make(
            resultado_curso__resultado=self.resultado,
            resultado_curso__curso=self.curso,
            inscricao=inscricao,
        )
        nao_ampla = models.Modalidade.objects.get(id=2)
        inscricao_nao_ampla = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=nao_ampla
        )
        resultado_inscricao_nao_ampla = recipes.resultado_preliminar_inscricao.make(
            resultado_curso__resultado=self.resultado,
            resultado_curso__curso=self.curso,
            inscricao=inscricao_nao_ampla,
        )
        inscricoes = self.resultado.get_inscricoes(self.curso, self.modalidade_ampla)
        self.assertIn(resultado_inscricao, inscricoes)
        self.assertIn(resultado_inscricao_nao_ampla, inscricoes)

    def test_get_inscricoes_deveria_aplicar_filtro_de_modalidade_para_nao_ampla(self):
        recipes.vagas_resultado_preliminar.make(
            resultado_curso__resultado=self.resultado,
            resultado_curso__curso=self.curso,
            modalidade=self.modalidade_ampla,
            quantidade=2,
        )
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=self.modalidade_ampla
        )
        resultado_inscricao = recipes.resultado_preliminar_inscricao.make(
            resultado_curso__resultado=self.resultado,
            resultado_curso__curso=self.curso,
            inscricao=inscricao,
        )
        modalidade_nao_ampla = models.Modalidade.objects.get(id=2)
        recipes.vagas_resultado_preliminar.make(
            resultado_curso__resultado=self.resultado,
            resultado_curso__curso=self.curso,
            modalidade=modalidade_nao_ampla,
        )
        inscricao_nao_ampla = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=modalidade_nao_ampla
        )
        resultado_inscricao_nao_ampla = recipes.resultado_preliminar_inscricao.make(
            resultado_curso__resultado=self.resultado,
            resultado_curso__curso=self.curso,
            inscricao=inscricao_nao_ampla,
        )
        inscricoes = self.resultado.get_inscricoes(self.curso, modalidade_nao_ampla)
        self.assertNotIn(resultado_inscricao, inscricoes)
        self.assertIn(resultado_inscricao_nao_ampla, inscricoes)

    def test_get_inscricoes_deveria_retornar_vagas_ate_o_limite_da_quantidade_definida(self):
        recipes.vagas_resultado_preliminar.make(
            resultado_curso__resultado=self.resultado,
            resultado_curso__curso=self.curso,
            modalidade=self.modalidade_ampla,
            quantidade=3
        )
        processo_inscricao = recipes.processo_inscricao.make()
        recipes.resultado_preliminar_inscricao.make(
            resultado_curso__resultado=self.resultado,
            resultado_curso__curso=self.curso,
            inscricao__edital=processo_inscricao.edital,
            _quantity=4
        )
        inscricoes = self.resultado.get_inscricoes(self.curso, self.modalidade_ampla)
        self.assertEqual(3, inscricoes.count())

    def test_get_vagas_deveria_retornar_corretamente_para_curso_modalidade_fornecido(self):
        vagas_expected = recipes.vagas_resultado_preliminar.make(
            resultado_curso__resultado=self.resultado,
            resultado_curso__curso=self.curso,
            modalidade=self.modalidade_ampla,
        )
        vagas = self.resultado.get_vagas(self.curso, self.modalidade_ampla)
        self.assertIsInstance(vagas, models.VagasResultadoPreliminar)
        self.assertEqual(vagas_expected, vagas)

    def test_get_resultado_inscricao_deveria_retornar_corretamente_para_inscricao_fornecida(self):
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=self.modalidade_ampla
        )
        resultado_expected = recipes.resultado_preliminar_inscricao.make(
            inscricao=inscricao,
            resultado_curso__resultado=self.resultado,
        )
        resultado_inscricao = self.resultado.get_resultado_inscricao(inscricao)
        self.assertIsInstance(resultado_inscricao, models.ResultadoPreliminarInscricao)
        self.assertEqual(resultado_expected, resultado_inscricao)

    def test_get_classificacao_deveria_retornar_geral_e_cota(self):
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=self.modalidade_ampla
        )
        resultado_inscricao = recipes.resultado_preliminar_inscricao.make(
            inscricao=inscricao,
            resultado_curso__resultado=self.resultado,
        )
        expected = resultado_inscricao.classificacao, resultado_inscricao.classificacao_cota
        self.assertEqual(expected, self.resultado.get_classificacao(inscricao))

    def test_get_ampla_deveria_retornar_modalidade_ampla_pre_definida(self):
        self.assertEqual(
            models.Modalidade.objects.get(equivalente_id=ModalidadeEnum.ampla_concorrencia),
            models.ResultadoPreliminar.get_ampla()
        )

    @mock.patch.object(models.VagasResultadoPreliminar, "get_classificados")
    def test_is_classificado_modalidade_deveria_ser_verdadeiro_quando_inscricao_classificada(
            self, get_classificados
    ):
        inscricao = recipes.inscricao.make(
            edital=self.edital, curso=self.curso, modalidade_cota=self.modalidade_ampla
        )
        recipes.vagas_resultado_preliminar.make(
            resultado_curso__resultado=self.resultado,
            resultado_curso__curso=self.curso,
            modalidade=self.modalidade_ampla,
        )
        resultado_inscricao = recipes.resultado_preliminar_inscricao.make(
            inscricao=inscricao,
            resultado_curso__resultado=self.resultado,
        )
        get_classificados.return_value = [resultado_inscricao]
        self.assertTrue(
            self.resultado.is_classificado_modalidade(inscricao, inscricao.modalidade_cota)
        )

    @mock.patch.object(models.ResultadoPreliminar, "is_classificado_modalidade")
    def test_is_classificado_deveria_retornar_verdadeiro_na_modalidade_ampla(
            self, is_classificado_modalidade
    ):
        is_classificado_modalidade.return_value = True
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=self.modalidade_ampla
        )
        self.assertTrue(self.resultado.is_classificado(inscricao))

    @mock.patch.object(models.ResultadoPreliminar, "is_classificado_modalidade")
    def test_is_classificado_deveria_retornar_verdadeiro_se_classificado_na_modalidade(
            self, is_classificado_modalidade
    ):
        is_classificado_modalidade.return_value = True
        modalidade_nao_ampla = ModalidadeEnum.escola_publica
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota_id=modalidade_nao_ampla
        )
        self.assertTrue(self.resultado.is_classificado(inscricao))

    @mock.patch.object(models.ResultadoPreliminar, "get_ampla")
    @mock.patch.object(models.ResultadoPreliminar, "is_classificado_modalidade")
    def test_is_classificado_deveria_retornar_falso_se_nao_classificado(
            self, is_classificado_modalidade, get_ampla
    ):
        is_classificado_modalidade.return_value = False
        modalidade_nao_ampla = ModalidadeEnum.escola_publica
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota_id=modalidade_nao_ampla
        )
        self.assertFalse(self.resultado.is_classificado(inscricao))

    @mock.patch.object(models.ResultadoPreliminar, "get_classificacao")
    @mock.patch.object(models.ResultadoPreliminar, "is_classificado")
    @mock.patch.object(models.ResultadoPreliminar, "get_vagas")
    def test_em_lista_espera_modalidade_deveria_ser_falso_para_classificado(
            self, get_vagas, is_classificado, get_classificacao
    ):
        is_classificado.return_value = True
        get_classificacao.return_value = 1, 1
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=self.modalidade_ampla
        )
        self.assertFalse(
            self.resultado.em_lista_espera_modalidade(inscricao, inscricao.modalidade_cota)
        )

    @mock.patch.object(models.ResultadoPreliminar, "get_classificacao")
    @mock.patch.object(models.ResultadoPreliminar, "is_classificado")
    @mock.patch.object(models.ResultadoPreliminar, "get_vagas")
    def test_em_lista_espera_modalidade_deveria_ser_falso_para_classificado_nao_ampla(
            self, get_vagas, is_classificado, get_classificacao
    ):
        is_classificado.return_value = True
        get_classificacao.return_value = 1, 1
        modalidade_nao_ampla = ModalidadeEnum.escola_publica
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota_id=modalidade_nao_ampla
        )
        self.assertFalse(
            self.resultado.em_lista_espera_modalidade(inscricao, inscricao.modalidade_cota)
        )

    @mock.patch.object(models.ResultadoPreliminar, "get_classificacao")
    @mock.patch.object(models.ResultadoPreliminar, "is_classificado")
    @mock.patch.object(models.ResultadoPreliminar, "get_vagas")
    def test_em_lista_espera_modalidade_deveria_ser_falso_se_classificacao_maior_que_limite(
            self, get_vagas, is_classificado, get_classificacao
    ):
        is_classificado.return_value = False
        get_vagas.return_value.get_limite_lista_espera.return_value = 1
        get_classificacao.return_value = 2, 1
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=self.modalidade_ampla)

        self.assertFalse(
            self.resultado.em_lista_espera_modalidade(inscricao, inscricao.modalidade_cota)
        )

    @mock.patch.object(models.ResultadoPreliminar, "get_classificacao")
    @mock.patch.object(models.ResultadoPreliminar, "is_classificado")
    @mock.patch.object(models.ResultadoPreliminar, "get_vagas")
    def test_em_lista_espera_modalidade_deveria_ser_verdade_se_classificacao_igual_limite(
            self, get_vagas, is_classificado, get_classificacao
    ):
        is_classificado.return_value = False
        get_vagas.return_value.get_limite_lista_espera.return_value = 1
        get_classificacao.return_value = 1, 1
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=self.modalidade_ampla
        )
        self.assertTrue(
            self.resultado.em_lista_espera_modalidade(inscricao, inscricao.modalidade_cota)
        )

    @mock.patch.object(models.ResultadoPreliminar, "get_classificacao")
    @mock.patch.object(models.ResultadoPreliminar, "is_classificado")
    @mock.patch.object(models.ResultadoPreliminar, "get_vagas")
    def test_em_lista_espera_modalidade_deveria_ser_verdade_se_classificacao_menor_que_limite(
            self, get_vagas, is_classificado, get_classificacao
    ):
        is_classificado.return_value = False
        get_vagas.return_value.get_limite_lista_espera.return_value = 2
        get_classificacao.return_value = 1, 1
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=self.modalidade_ampla
        )
        self.assertTrue(
            self.resultado.em_lista_espera_modalidade(inscricao, inscricao.modalidade_cota)
        )

    @mock.patch.object(models.ResultadoPreliminar, "get_classificacao")
    @mock.patch.object(models.ResultadoPreliminar, "is_classificado")
    @mock.patch.object(models.ResultadoPreliminar, "get_vagas")
    def test_em_lista_espera_modalidade_deveria_ser_falso_se_classificacao_maior_que_limite_cota(
            self, get_vagas, is_classificado, get_classificacao
    ):
        is_classificado.return_value = False
        get_vagas.return_value.get_limite_lista_espera.return_value = 1
        get_classificacao.return_value = 1, 2
        modalidade_nao_ampla = ModalidadeEnum.escola_publica
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota_id=modalidade_nao_ampla
        )
        self.assertFalse(
            self.resultado.em_lista_espera_modalidade(inscricao, inscricao.modalidade_cota)
        )

    @mock.patch.object(models.ResultadoPreliminar, "get_classificacao")
    @mock.patch.object(models.ResultadoPreliminar, "is_classificado")
    @mock.patch.object(models.ResultadoPreliminar, "get_vagas")
    def test_em_lista_espera_modalidade_deveria_ser_verdade_se_classificacao_igual_limite_cota(
            self, get_vagas, is_classificado, get_classificacao
    ):
        is_classificado.return_value = False
        get_vagas.return_value.get_limite_lista_espera.return_value = 3
        get_classificacao.return_value = 1, 3
        modalidade_nao_ampla = ModalidadeEnum.escola_publica
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota_id=modalidade_nao_ampla
        )
        self.assertTrue(
            self.resultado.em_lista_espera_modalidade(inscricao, inscricao.modalidade_cota)
        )

    @mock.patch.object(models.ResultadoPreliminar, "get_classificacao")
    @mock.patch.object(models.ResultadoPreliminar, "is_classificado")
    @mock.patch.object(models.ResultadoPreliminar, "get_vagas")
    def test_em_lista_espera_modalidade_deveria_ser_verdade_se_classificacao_menor_que_limite_cota(
            self, get_vagas, is_classificado, get_classificacao
    ):
        is_classificado.return_value = False
        get_vagas.return_value.get_limite_lista_espera.return_value = 3
        get_classificacao.return_value = 1, 2
        modalidade_nao_ampla = ModalidadeEnum.escola_publica
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota_id=modalidade_nao_ampla
        )
        self.assertTrue(
            self.resultado.em_lista_espera_modalidade(inscricao, inscricao.modalidade_cota)
        )

    @mock.patch.object(models.ResultadoPreliminar, "em_lista_espera_modalidade")
    def test_em_lista_espera_deveria_ser_falso_para_ampla(self, em_lista_espera_modalidade):
        em_lista_espera_modalidade.return_value = False
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=self.modalidade_ampla
        )
        self.assertFalse(self.resultado.em_lista_espera(inscricao))

    @mock.patch.object(models.ResultadoPreliminar, "em_lista_espera_modalidade")
    def test_em_lista_espera_deveria_ser_verdade_para_ampla(
            self, em_lista_espera_modalidade
    ):
        em_lista_espera_modalidade.return_value = True
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=self.modalidade_ampla
        )
        self.assertTrue(self.resultado.em_lista_espera(inscricao))

    @mock.patch.object(models.ResultadoPreliminar, "em_lista_espera_modalidade")
    def test_em_lista_espera_deveria_ser_verdade_para_sua_modalidade(
            self, em_lista_espera_modalidade
    ):
        em_lista_espera_modalidade.return_value = True
        modalidade_nao_ampla = ModalidadeEnum.escola_publica
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota_id=modalidade_nao_ampla
        )
        self.assertTrue(self.resultado.em_lista_espera(inscricao))

    @mock.patch.object(models.ResultadoPreliminar, "em_lista_espera_modalidade")
    def test_em_lista_espera_deveria_verificar_situacao_na_ampla_se_eh_inscricao_em_cota(
            self, em_lista_espera_modalidade
    ):
        em_lista_espera_modalidade.return_value = False
        modalidade_nao_ampla = ModalidadeEnum.escola_publica
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota_id=modalidade_nao_ampla
        )
        self.resultado.em_lista_espera(inscricao)
        modalidade_cota_verificada = em_lista_espera_modalidade.call_args_list[0][0][1]
        self.assertEqual(inscricao.modalidade_cota, modalidade_cota_verificada)
        ampla = models.Modalidade.objects.get(id=ModalidadeEnum.ampla_concorrencia)
        modalidade_ampla_verificada = em_lista_espera_modalidade.call_args_list[1][0][1]
        self.assertEqual(ampla, modalidade_ampla_verificada)

    def test_get_indeferimento_deveria_retornar_none_se_nao_ha_indeferimento(self):
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=self.modalidade_ampla
        )
        self.assertIsNone(self.resultado.get_indeferimento(inscricao))

    def test_get_indeferimento_deveria_retornar_justificativa_se_ha_indeferimento(self):
        inscricao = recipes.inscricao.make(
            edital=self.edital, modalidade_cota=self.modalidade_ampla
        )
        indeferimento = recipes.resultado_preliminar_inscricao_indeferida.make(
            resultado=self.resultado,
            inscricao=inscricao,
        )
        self.assertEqual(
            indeferimento.justiticativa_indeferimento,
            self.resultado.get_indeferimento(inscricao)
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.campus_patcher.stop()
        cls.fase_analise_patcher.stop()


class ResultadoPreliminarHomologadoTestCase(TestCase):
    def test_str_deveria_estar_corretamente_configurado(self):
        resultado = recipes.resultado_preliminar_homologado.prepare()
        self.assertEqual(
            f"Resultado Preliminar do {resultado.edital}",
            str(resultado)
        )

    def test_is_final_sempre_eh_falso(self):
        resultado = models.ResultadoPreliminarHomologado()
        self.assertFalse(resultado.is_final())


class ResultadoFinalTestCase(TestCase):

    def test_is_final_sempre_eh_verdade(self):
        resultado = models.ResultadoFinal()
        self.assertTrue(resultado.is_final())


class VagasResultadoPreliminarTestCase(TestCase):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.campus_patcher = mock.patch.multiple(
            cursos.models.Campus,
            cria_usuarios_diretores=mock.DEFAULT,
            adiciona_permissao_diretores=mock.DEFAULT,
            remove_permissao_diretores=mock.DEFAULT
        )
        cls.fase_analise_patcher = mock.patch.multiple(
            models.FaseAnalise,
            atualizar_grupos_permissao=mock.DEFAULT,
        )
        cls.campus_patcher.start()
        cls.fase_analise_patcher.start()

    def test_get_vagas_edital_deveria_retornar_modalidade_vagas_curso_edital(self):
        vagas = recipes.vagas_resultado_preliminar.make()
        modalidade = recipes.modalidade_vaga_curso_edital.make(
            modalidade=vagas.modalidade,
            curso_edital__curso=vagas.resultado_curso.curso,
            curso_edital__edital=vagas.resultado_curso.resultado.fase.edital,
        )
        self.assertEqual(modalidade, vagas.get_vagas_edital())

    @mock.patch.object(models.VagasResultadoPreliminar, "get_classificados")
    def test_get_vagas_resultado_deveria_retornar_numero_de_classificados(self, get_classificados):
        get_classificados.return_value.count.return_value = 1
        vagas = recipes.vagas_resultado_preliminar.make()
        self.assertEqual(1, vagas.get_vagas_resultado())

    def test_get_limite_lista_espera_deveria_retornar_quantidade_vagas_vezes_multiplicador(self):
        vagas = recipes.vagas_resultado_preliminar.make()
        edital = vagas.resultado_curso.resultado.fase.edital
        edital.processo_inscricao = recipes.processo_inscricao.make(edital=edital, multiplicador=2)
        recipes.modalidade_vaga_curso_edital.make(
            modalidade=vagas.modalidade,
            curso_edital__curso=vagas.resultado_curso.curso,
            curso_edital__edital=edital,
            quantidade_vagas=5
        )
        self.assertEqual(5 * 2, vagas.get_limite_lista_espera())

    @mock.patch("psct.export.get_inscricoes")
    def test_classificados_deveria_retornar_resultado_preliminar_das_inscricoes(
            self, get_inscricoes
    ):
        processo_inscricao = recipes.processo_inscricao.make()
        expected_classificados = [
            recipes.resultado_preliminar_inscricao.make(
                inscricao__edital=processo_inscricao.edital,
            )
        ]
        get_inscricoes.return_value = expected_classificados
        vagas = recipes.vagas_resultado_preliminar.make()
        self.assertEqual(
            expected_classificados,
            vagas.get_classificados()
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.campus_patcher.stop()
        cls.fase_analise_patcher.stop()
