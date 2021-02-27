from unittest import mock

from django.test import TestCase

import editais.tests.recipes
from base.tests.mixins import UserTestMixin
from cursos.tests.mixins import DiretorEnsinoPermissionData
from . import recipes
from ..templatetags import processoseletivo_tags as tags


class VagasPorCursoTestCase(DiretorEnsinoPermissionData, TestCase):
    def test_deveria_retornar_zero_vagas(self):
        chamada = recipes.chamada.make(vagas=0)
        vagas = tags.vagas_por_curso_na_etapa(chamada.etapa, chamada.curso)
        self.assertEqual(0, vagas)

    def test_deveria_retornar_duas_vagas(self):
        chamada = recipes.chamada.make(vagas=2)
        vagas = tags.vagas_por_curso_na_etapa(chamada.etapa, chamada.curso)
        self.assertEqual(2, vagas)


class VagasPorCampusTestCase(DiretorEnsinoPermissionData, TestCase):
    def test_deveria_retornar_zero_vagas_disponiveis_no_campus(self):
        chamada = recipes.chamada.make(vagas=0)
        vagas = tags.vagas_por_campus(chamada.etapa, chamada.curso.campus)
        self.assertEqual(0, vagas)

    def test_deveria_retornar_duas_vagas_disponiveis_no_campus(self):
        chamada = recipes.chamada.make(vagas=2)
        vagas = tags.vagas_por_campus(chamada.etapa, chamada.curso.campus)
        self.assertEqual(2, vagas)


class ConvocacoesAbertasTestCase(DiretorEnsinoPermissionData, UserTestMixin, TestCase):
    def test_deveria_retornar_nenhuma_convocacao_aberta_para_o_usuario(self):
        self.assertFalse(tags.get_convocacoes_abertas(self.usuario_base).exists())

    def test_deveria_retornar_nenhuma_convocacao_aberta_com_etapa_encerrada(self):
        etapa = recipes.etapa.make(encerrada=True, publica=True)
        chamada = recipes.chamada.make(etapa=etapa)
        inscricao = recipes.inscricao.make(chamada=chamada)
        self.assertFalse(tags.get_convocacoes_abertas(inscricao.candidato.pessoa.user).exists())

    def test_deveria_retornar_nenhuma_convocacao_aberta_com_etapa_nao_publica(self):
        etapa = recipes.etapa.make(encerrada=False, publica=False)
        chamada = recipes.chamada.make(etapa=etapa)
        inscricao = recipes.inscricao.make(chamada=chamada)
        self.assertFalse(
            tags.get_convocacoes_abertas(inscricao.candidato.pessoa.user).exists()
        )

    def test_deveria_retornar_inscricao_com_convocacao_aberta(self):
        etapa = recipes.etapa.make(encerrada=False, publica=True)
        chamada = recipes.chamada.make(etapa=etapa)
        inscricao = recipes.inscricao.make(chamada=chamada)
        self.assertTrue(
            tags.get_convocacoes_abertas(inscricao.candidato.pessoa.user)
            .filter(id=inscricao.id)
            .exists()
        )


class VagasPorCursoNaModalidadeTestCase(DiretorEnsinoPermissionData, TestCase):
    def test_deveria_retornar_zero_vagas(self):
        chamada = recipes.chamada.make(vagas=0)
        vagas = tags.vagas_por_curso_na_modalidade(
            chamada.etapa, chamada.curso, chamada.modalidade
        )
        self.assertEqual(0, vagas)

    def test_deveria_retornar_duas_vagas(self):
        chamada = recipes.chamada.make(vagas=2)
        vagas = tags.vagas_por_curso_na_modalidade(
            chamada.etapa, chamada.curso, chamada.modalidade
        )
        self.assertEqual(2, vagas)


class MatriculadoEmChamadaTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.inscricao = recipes.inscricao.make()

    def test_inscricao_nao_deveria_estar_matriculada(self):
        recipes.matricula.make(inscricao=self.inscricao)  # matrícula em outra etapa
        self.assertFalse(
            tags.matriculado_em_chamada(self.inscricao, self.inscricao.chamada.etapa)
        )

    def test_inscricao_deveria_estar_matriculada(self):
        recipes.matricula.make(
            inscricao=self.inscricao, etapa=self.inscricao.chamada.etapa
        )
        self.assertTrue(
            tags.matriculado_em_chamada(self.inscricao, self.inscricao.chamada.etapa)
        )


class SituacaoMatriculaEmChamadaTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.inscricao = recipes.inscricao.make()

    @mock.patch("processoseletivo.models.Inscricao.get_situacao_matricula_em_chamada")
    def test_deveria_retornar_nao_compareceu(self, get_situacao):
        get_situacao.return_value = "Não compareceu"
        situacao = tags.situacao_matricula_em_chamada(
            self.inscricao, self.inscricao.chamada.etapa
        )
        self.assertEqual("Não compareceu", situacao)

    @mock.patch("processoseletivo.models.Inscricao.get_situacao_matricula_em_chamada")
    def test_deveria_retornar_matriculado(self, get_situacao):
        get_situacao.return_value = "Matriculado(a)"
        situacao = tags.situacao_matricula_em_chamada(
            self.inscricao, self.inscricao.chamada.etapa
        )
        self.assertEqual("Matriculado(a)", situacao)

    @mock.patch("processoseletivo.models.Inscricao.get_situacao_matricula_em_chamada")
    def test_deveria_retornar_lista_de_espera(self, get_situacao):
        get_situacao.return_value = "Lista de Espera"
        situacao = tags.situacao_matricula_em_chamada(
            self.inscricao, self.inscricao.chamada.etapa
        )
        self.assertEqual("Lista de Espera", situacao)

    @mock.patch("processoseletivo.models.Inscricao.get_situacao_matricula_em_chamada")
    def test_deveria_retornar_lista_documentacao_indeferida(self, get_situacao):
        get_situacao.return_value = "Doc. Indeferida"
        situacao = tags.situacao_matricula_em_chamada(
            self.inscricao, self.inscricao.chamada.etapa
        )
        self.assertEqual("Doc. Indeferida", situacao)


class ConfirmacaoInteresseEmChamadaTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.inscricao = recipes.inscricao.make()

    def test_inscricao_nao_deveria_ter_confirmacao_interesse(self):
        self.assertFalse(
            tags.confirmou_interesse_em_chamada(
                self.inscricao, self.inscricao.chamada.etapa
            )
        )

    def test_inscricao_deveria_ter_confirmacao_interesse(self):
        recipes.confirmacao.make(
            inscricao=self.inscricao, etapa=self.inscricao.chamada.etapa
        )
        self.assertTrue(
            tags.confirmou_interesse_em_chamada(
                self.inscricao, self.inscricao.chamada.etapa
            )
        )


class EtapaAbertaTestCase(DiretorEnsinoPermissionData, TestCase):
    def test_nao_deveria_ter_etapa_aberta(self):
        recipes.etapa.make(encerrada=True)
        self.assertFalse(tags.has_etapa_aberta())

    def test_deveria_ter_etapa_aberta(self):
        recipes.etapa.make(encerrada=False)
        self.assertTrue(tags.has_etapa_aberta())


class EtapaAberturaTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.edicao = recipes.edicao.make()

    def test_edicao_nao_deveria_ter_edital_abertura(self):
        self.assertIsNone(tags.get_edital(self.edicao))

    def test_edicao_deveria_ter_edital_abertura(self):
        edital = editais.tests.recipes.edital.make(edicao=self.edicao, tipo="ABERTURA")
        self.assertEqual(edital, tags.get_edital(self.edicao))


class ModalidadeEnsinoFundamentalTestCase(DiretorEnsinoPermissionData, TestCase):
    def test_deveria_mudar_nome_da_modalidade_ensino_medio_para_fundamental(self):
        modalidade = tags.get_modalidade_ensino_fundamental("ensino médio")
        self.assertEqual("ensino fundamental", modalidade)

    def test_nao_deveria_mudar_nome_modalidade(self):
        modalidade = tags.get_modalidade_ensino_fundamental("ensino superior")
        self.assertEqual("ensino superior", modalidade)
