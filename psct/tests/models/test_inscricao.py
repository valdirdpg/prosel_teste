import datetime
from unittest import expectedFailure, mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time

import base.tests.recipes
import cursos.models
import cursos.recipes
import editais.tests.recipes
import processoseletivo.tests.recipes
from cursos.choices import Formacao
from cursos.tests.mixins import DiretorEnsinoPermissionData
from processoseletivo.models import ModalidadeEnum, Modalidade
from .. import models
from .. import recipes
from ... import pdf


class ProcessoInscricaoTestCase(TestCase):

    def test_pode_alterar_funcao_segunda_opcao_deveria_ser_verdade_se_nao_ha_inscricao(self):
        processo_inscricao = recipes.processo_inscricao.make()
        self.assertTrue(processo_inscricao.pode_alterar_funcao_segunda_opcao)

    def test_pode_alterar_funcao_segunda_opcao_deveria_ser_falso_se_ha_inscricao(self):
        processo_inscricao = recipes.processo_inscricao.make()
        with mock.patch.multiple(
                cursos.models.Campus,
                cria_usuarios_diretores=mock.DEFAULT,
                adiciona_permissao_diretores=mock.DEFAULT,
                remove_permissao_diretores=mock.DEFAULT,
        ):
            recipes.inscricao.make(edital=processo_inscricao.edital)
        self.assertFalse(processo_inscricao.pode_alterar_funcao_segunda_opcao)

    @mock.patch.object(
        models.ProcessoInscricao,
        "pode_alterar_funcao_segunda_opcao",
        new_callable=mock.PropertyMock
    )
    def test_clean_deveria_validar_mudanca_no_possui_segunda_opcao(
            self, pode_alterar_funcao_segunda_opcao
    ):
        pode_alterar_funcao_segunda_opcao.return_value = False
        processo_inscricao = recipes.processo_inscricao.make(possui_segunda_opcao=True)
        processo_inscricao.possui_segunda_opcao = False
        with self.assertRaises(ValidationError) as cm:
            processo_inscricao.clean()
        self.assertIn(
            "Este valor não pode ser alterado porque já existem inscrições associadas ao edital.",
            cm.exception.message_dict.get("possui_segunda_opcao"),
        )

    @mock.patch.object(
        models.ProcessoInscricao,
        "pode_alterar_funcao_segunda_opcao",
        new_callable=mock.PropertyMock
    )
    def test_clean_nao_deveria_validar_se_possui_segunda_opcao_nao_mudar(
            self, pode_alterar_funcao_segunda_opcao
    ):
        pode_alterar_funcao_segunda_opcao.return_value = False
        processo_inscricao = recipes.processo_inscricao.make(possui_segunda_opcao=True)
        processo_inscricao.possui_segunda_opcao = True
        self.assertIsNone(processo_inscricao.clean())

    def test_clean_nao_deveria_validar_objeto_esta_sendo_criado(self):
        processo_inscricao = recipes.processo_inscricao.prepare()
        self.assertIsNone(processo_inscricao.clean())

    def test_str_deve_conter_o_edital(self):
        processo_inscricao = recipes.processo_inscricao.make()
        self.assertEqual(f"Cursos do {processo_inscricao.edital}", str(processo_inscricao))

    def test_property_em_periodo_inscricao_deve_retornar_verdadeiro(self):
        processo_inscricao = recipes.processo_inscricao.make()
        self.assertTrue(processo_inscricao.em_periodo_inscricao)

    def test_property_em_periodo_inscricao_deve_retornar_falso_se_data_inicio_for_maior_que_hoje(
            self
    ):
        inicio = datetime.date.today() + datetime.timedelta(days=1)
        processo_inscricao = recipes.processo_inscricao.make(
            data_inicio=inicio
        )
        self.assertFalse(processo_inscricao.em_periodo_inscricao)

    def test_property_em_periodo_inscricao_deve_retornar_falso_se_data_fim_for_menor_que_hoje(self):
        encerramento = datetime.date.today() - datetime.timedelta(days=1)
        processo_inscricao = recipes.processo_inscricao.make(
            data_encerramento=encerramento,
        )
        self.assertFalse(processo_inscricao.em_periodo_inscricao)

    def test_pode_emitir_comprovante_deve_retornar_verdadeiro_sem_data_final(self):
        processo_inscricao = recipes.processo_inscricao.make(
            data_inicial_comprovante=datetime.datetime.now
        )
        self.assertTrue(processo_inscricao.pode_emitir_comprovante)

    def test_pode_emitir_comprovante_deve_retornar_verdadeiro_com_data_final(self):
        final = datetime.datetime.now() + datetime.timedelta(days=1)
        processo_inscricao = recipes.processo_inscricao.make(
            data_inicial_comprovante=datetime.datetime.now,
            data_final_comprovante=final,
        )
        self.assertTrue(processo_inscricao.pode_emitir_comprovante)

    def test_pode_emitir_comprovante_deve_retornar_falso_se_nao_ha_data_inicial_comprovante(
            self
    ):
        processo_inscricao = recipes.processo_inscricao.make(
        )
        self.assertFalse(processo_inscricao.pode_emitir_comprovante)

    @freeze_time(datetime.datetime.now())
    def test_pode_emitir_comprovante_deve_retornar_falso_quando_data_inicial_maior_que_agora(
            self
    ):
        inicial = datetime.datetime.now() + datetime.timedelta(minutes=1)
        processo_inscricao = recipes.processo_inscricao.make(
            data_inicial_comprovante=inicial,
        )
        self.assertFalse(processo_inscricao.pode_emitir_comprovante)

    @freeze_time(datetime.datetime.now())
    def test_pode_emitir_comprovante_deve_retornar_falso_quando_data_final_tiver_passado(
            self
    ):
        inicial = datetime.datetime.now() - datetime.timedelta(days=1)
        final = datetime.datetime.now() - datetime.timedelta(minutes=1)
        processo_inscricao = recipes.processo_inscricao.make(
            data_inicial_comprovante=inicial,
            data_final_comprovante=final,
        )
        self.assertFalse(processo_inscricao.pode_emitir_comprovante)

    def test_pode_acompanhar_inscricao_deve_retornar_verdadeiro_se_periodo_inscricao_encerrou(
            self
    ):
        encerramento = datetime.date.today() - datetime.timedelta(days=1)
        processo_inscricao = recipes.processo_inscricao.make(
            data_encerramento=encerramento
        )
        self.assertTrue(processo_inscricao.pode_acompanhar_inscricao)

    @expectedFailure  # Propriedade está implementada de maneira errada
    def test_pode_acompanhar_inscricao_deve_retornar_falso_se_periodo_inscricao_nao_encerrou(
            self
    ):
        self.assertFalse(self.processo_inscricao.pode_acompanhar_inscricao)

    def test_clean_deve_validar_data_inicial_comprovante_menor_igual_a_data_encerramento_inscricoes(
            self
    ):
        data_inicial_comprovante = datetime.datetime.today()
        processo_inscricao = recipes.processo_inscricao.make(
            data_encerramento=data_inicial_comprovante.date(),
            data_inicial_comprovante=data_inicial_comprovante,
        )
        with self.assertRaises(ValidationError) as ex:
            processo_inscricao.clean()
            self.assertIn(
                (
                    "A data inicial de emissão de comprovante não pode ser igual ou inferior"
                    " à data de encerramento."
                ),
                ex.exception.message_dict.get("data_inicial_comprovante"),
            )

    def test_clean_deve_validar_data_final_comprovante_menor_igual_a_data_encerramento_inscricoes(
            self
    ):
        data_final_comprovante = datetime.datetime.now()
        processo_inscricao = recipes.processo_inscricao.make(
            data_encerramento=data_final_comprovante.date(),
            data_final_comprovante=data_final_comprovante,
        )
        with self.assertRaises(ValidationError) as ex:
            processo_inscricao.clean()
            self.assertIn(
                (
                    "A data final de emissão de comprovante não pode ser igual ou anterior"
                    " à data de encerramento."
                ),
                ex.exception.message_dict.get("data_final_comprovante"),
            )

    def test_clean_deve_validar_data_inicial_comprovante_menor_que_a_data_final_comprovante(
            self
    ):
        data_inicial_comprovante = datetime.datetime.now() + datetime.timedelta(days=1)
        processo_inscricao = recipes.processo_inscricao.make(
            edital=editais.tests.recipes.edital.make,
            data_inicial_comprovante=data_inicial_comprovante,
            data_final_comprovante=data_inicial_comprovante,
        )
        with self.assertRaises(ValidationError) as ex:
            processo_inscricao.clean()
            self.assertIn(
                (
                    "A data final de emissão de comprovante não pode ser igual ou anterior"
                    " à data de encerramento."
                ),
                ex.exception.message_dict.get("data_inicial_comprovante"),
            )

    def test_clean_deve_validar_data_resultado_preliminar_posterior_a_data_encerramento_inscricoes(
            self
    ):
        data_encerramento = datetime.date.today() + datetime.timedelta(days=1)
        data_resultado_preliminar = datetime.datetime.now()
        processo_inscricao = recipes.processo_inscricao.make(
            data_encerramento=data_encerramento,
            data_resultado_preliminar=data_resultado_preliminar,
        )
        with self.assertRaises(ValidationError) as ex:
            processo_inscricao.clean()
            self.assertIn(
                "A Data do resultado preliminar deve ser superior à data de encerramento",
                ex.exception.message_dict.get("data_resultado_preliminar"),
            )


class ModalidadeTestCase(TestCase):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json"
    ]

    def test_str_deve_conter_texto(self):
        modalidade = recipes.modalidade.make(
        )
        self.assertEqual(modalidade.texto, str(modalidade))

    def test_str_deve_conter_nome_modalidade_equivalente(self):
        modalidade = recipes.modalidade.make(
            texto="",
        )
        self.assertEqual(modalidade.equivalente.nome, str(modalidade))

    def test_is_ampla_deve_retornar_falso(self):
        modalidade_processo_seletivo = Modalidade.objects.exclude(
            pk=ModalidadeEnum.ampla_concorrencia
        ).first()
        modalidade_nao_ampla = recipes.modalidade.make(equivalente=modalidade_processo_seletivo)
        self.assertFalse(modalidade_nao_ampla.is_ampla)

    def test_resumo_deve_retornar_resumo_da_modalidade_equivalente(self):
        modalidade = recipes.modalidade.make(
            texto="",
            equivalente=processoseletivo.tests.recipes.modalidade.make
        )
        self.assertEqual(modalidade.equivalente.resumo, modalidade.resumo)

    def test_resumo_deve_retornar_str_da_modalidade(self):
        modalidade_equivalente = processoseletivo.tests.recipes.modalidade.make(resumo="")
        modalidade = recipes.modalidade.make(equivalente=modalidade_equivalente)
        self.assertEqual(str(modalidade), modalidade.resumo)


class InscricaoTestCase(TestCase):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]
    campus_patcher: mock.patch.multiple
    fase_analise_patcher: mock.patch.multiple

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.campus_patcher = mock.patch.multiple(
            cursos.models.Campus,
            cria_usuarios_diretores=mock.DEFAULT,
            adiciona_permissao_diretores=mock.DEFAULT,
            remove_permissao_diretores=mock.DEFAULT,
        )
        cls.fase_analise_patcher = mock.patch.multiple(
            models.FaseAnalise,
            atualizar_grupos_permissao=mock.DEFAULT,
        )
        cls.campus_patcher.start()
        cls.fase_analise_patcher.start()
        cls.processo_inscricao = recipes.processo_inscricao.make(
            formacao=Formacao.SUBSEQUENTE.name
        )
        cls.edital = cls.processo_inscricao.edital

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.campus_patcher.stop()
        cls.fase_analise_patcher.stop()

    def test_str_deve_conter_candidato_e_edital(self):
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertEqual(
            f"Inscrição de {inscricao.candidato} em {inscricao.edital}",
            str(inscricao)
        )

    def test_property_inscricao_pre_analise_deve_retornar_inscricao_usada_na_analise(self):
        inscricao_pre_analise = recipes.inscricao_pre_analise.make(
            fase__edital=self.edital
        )
        inscricao = recipes.inscricao.make(
            candidato=inscricao_pre_analise.candidato,
            edital=inscricao_pre_analise.fase.edital,
            curso=inscricao_pre_analise.curso,
            modalidade_cota=inscricao_pre_analise.modalidade
        )
        self.assertEqual(inscricao_pre_analise, inscricao.inscricao_pre_analise)

    def test_property_inscricao_pre_analise_deve_retornar_vazio_quando_inscricao_nao_foi_importada(
            self
    ):
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertIsNone(inscricao.inscricao_pre_analise)

    def test_is_integrado_deve_retornar_verdadeiro(self):
        curso = recipes.curso_selecao.make(formacao=Formacao.INTEGRADO.name)
        inscricao = recipes.inscricao.make(edital=self.edital, curso=curso)
        self.assertTrue(inscricao.is_integrado)

    def test_is_integrado_deve_retornar_falso(self):
        curso = recipes.curso_selecao.make(formacao=Formacao.SUBSEQUENTE.name)
        inscricao = recipes.inscricao.make(edital=self.edital, curso=curso)
        self.assertFalse(inscricao.is_integrado)

    def test_em_periodo_inscricao_deve_retornar_verdadeiro(self):
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertTrue(inscricao.em_periodo_inscricao)

    def test_em_periodo_inscricao_deve_retornar_falso_quando_inicio_for_maior_que_hoje(
            self
    ):
        data_inicio = datetime.date.today() + datetime.timedelta(days=1)
        processo_inscricao = recipes.processo_inscricao.make(data_inicio=data_inicio)
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.assertFalse(inscricao.em_periodo_inscricao)

    def test_em_periodo_inscricao_deve_retornar_falso_quando_encerramento_for_menor_que_hoje(
            self
    ):
        data_encerramento = datetime.date.today() - datetime.timedelta(days=1)
        processo_inscricao = recipes.processo_inscricao.make(data_encerramento=data_encerramento)
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.assertFalse(inscricao.em_periodo_inscricao)

    @mock.patch('psct.models.Inscricao.is_cancelada', new_callable=mock.PropertyMock)
    @mock.patch('psct.models.Inscricao.em_periodo_inscricao', new_callable=mock.PropertyMock)
    def test_pode_alterar_deve_retornar_verdadeiro(
            self, em_periodo_inscricao, is_cancelada
    ):
        em_periodo_inscricao.return_value = True
        is_cancelada.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertTrue(inscricao.pode_alterar)

    @mock.patch('psct.models.Inscricao.is_cancelada', new_callable=mock.PropertyMock)
    @mock.patch('psct.models.Inscricao.em_periodo_inscricao', new_callable=mock.PropertyMock)
    def test_pode_alterar_deve_retornar_falso_quando_nao_for_periodo_de_inscricao(
            self, em_periodo_inscricao, is_cancelada
    ):
        em_periodo_inscricao.return_value = False
        is_cancelada.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertFalse(inscricao.pode_alterar)

    @mock.patch('psct.models.Inscricao.is_cancelada', new_callable=mock.PropertyMock)
    @mock.patch('psct.models.Inscricao.em_periodo_inscricao', new_callable=mock.PropertyMock)
    def test_pode_alterar_deve_retornar_falso_quando_inscricao_estiver_cancelada(
            self, em_periodo_inscricao, is_cancelada
    ):
        em_periodo_inscricao.return_value = True
        is_cancelada.return_value = True
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertFalse(inscricao.pode_alterar)

    def test_is_cancelada_deve_retornar_verdadeiro(self):
        inscricao = recipes.inscricao.make(edital=self.edital)
        recipes.cancelamento_inscricao.make(inscricao=inscricao)
        self.assertTrue(inscricao.is_cancelada)

    def test_is_cancelada_deve_retornar_falso(self):
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertFalse(inscricao.is_cancelada)

    def test_is_apagou_notas_deve_retornar_verdadeiro(self):
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=False)
        recipes.comprovante.make(inscricao=inscricao)
        self.assertTrue(inscricao.is_apagou_notas)

    def test_is_apagou_notas_deve_retornar_falso_se_inscricao_nao_possuir_comprovantes(
            self
    ):
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=False)
        self.assertFalse(inscricao.is_apagou_notas)

    def test_is_apagou_notas_deve_retornar_falso_quando_aceite_estiver_marcado(self):
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=True)
        recipes.comprovante.make(inscricao=inscricao)
        self.assertFalse(inscricao.is_apagou_notas)

    @mock.patch(
        'psct.models.ProcessoInscricao.pode_emitir_comprovante', new_callable=mock.PropertyMock
    )
    def test_is_periodo_deferimento_deve_retornar_verdadeiro(
            self, pode_emitir_comprovante
    ):
        pode_emitir_comprovante.return_value = True
        processo_inscricao = recipes.processo_inscricao.make()
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.assertTrue(inscricao.is_periodo_deferimento)

    @mock.patch(
        'psct.models.ProcessoInscricao.pode_emitir_comprovante', new_callable=mock.PropertyMock
    )
    def test_is_periodo_deferimento_deve_retornar_falso(self, pode_emitir_comprovante):
        pode_emitir_comprovante.return_value = False
        processo_inscricao = recipes.processo_inscricao.make()
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.assertFalse(inscricao.is_periodo_deferimento)

    @mock.patch('psct.models.Inscricao.is_cancelada', new_callable=mock.PropertyMock)
    @mock.patch('psct.models.Inscricao.is_periodo_deferimento', new_callable=mock.PropertyMock)
    def test_is_deferida_deve_retornar_verdadeiro(
            self, is_periodo_deferimento, is_cancelada
    ):
        is_periodo_deferimento.return_value = True
        is_cancelada.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=True)
        recipes.comprovante.make(inscricao=inscricao)
        self.assertTrue(inscricao.is_deferida)

    @mock.patch('psct.models.Inscricao.is_cancelada', new_callable=mock.PropertyMock)
    @mock.patch('psct.models.Inscricao.is_periodo_deferimento', new_callable=mock.PropertyMock)
    def test_is_deferida_deve_retornar_falso_quando_nao_for_periodo_de_deferimento(
            self, is_periodo_deferimento, is_cancelada
    ):
        is_periodo_deferimento.return_value = False
        is_cancelada.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=True)
        recipes.comprovante.make(inscricao=inscricao)
        self.assertFalse(inscricao.is_deferida)

    @mock.patch('psct.models.Inscricao.is_cancelada', new_callable=mock.PropertyMock)
    @mock.patch('psct.models.Inscricao.is_periodo_deferimento', new_callable=mock.PropertyMock)
    def test_is_deferida_deve_retornar_falso_quando_se_inscricao_nao_possuir_comprovantes(
            self, is_periodo_deferimento, is_cancelada
    ):
        is_periodo_deferimento.return_value = True
        is_cancelada.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=True)
        self.assertFalse(inscricao.is_deferida)

    @mock.patch('psct.models.Inscricao.is_cancelada', new_callable=mock.PropertyMock)
    @mock.patch('psct.models.Inscricao.is_periodo_deferimento', new_callable=mock.PropertyMock)
    def test_is_deferida_deve_retornar_falso_quando_aceite_nao_estiver_marcado(
            self, is_periodo_deferimento, is_cancelada
    ):
        is_periodo_deferimento.return_value = False
        is_cancelada.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=False)
        recipes.comprovante.make(inscricao=inscricao)
        self.assertFalse(inscricao.is_deferida)

    @mock.patch('psct.models.Inscricao.is_cancelada', new_callable=mock.PropertyMock)
    @mock.patch('psct.models.Inscricao.is_periodo_deferimento', new_callable=mock.PropertyMock)
    def test_is_deferida_deve_retornar_falso_quando_inscricao_estiver_cancelada(
            self, is_periodo_deferimento, is_cancelada
    ):
        is_periodo_deferimento.return_value = True
        is_cancelada.return_value = True
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=True)
        recipes.comprovante.make(inscricao=inscricao)
        self.assertFalse(inscricao.is_deferida)

    def test_is_ampla_concorrencia_deve_retornar_verdadeiro(self):
        modalidade_ampla = models.Modalidade.objects.get(
            equivalente=ModalidadeEnum.ampla_concorrencia
        )
        inscricao = recipes.inscricao.make(edital=self.edital, modalidade_cota=modalidade_ampla)
        self.assertTrue(inscricao.is_ampla_concorrencia)

    def test_is_ampla_concorrencia_deve_retornar_falso(self):
        modalidade_cota = models.Modalidade.objects.get(equivalente=ModalidadeEnum.cota_racial)
        inscricao = recipes.inscricao.make(edital=self.edital, modalidade_cota=modalidade_cota)
        self.assertFalse(inscricao.is_ampla_concorrencia)

    @mock.patch('psct.models.Inscricao.get_resultado_edital')
    def test_is_resultado_final_deve_retornar_verdadeiro(self, get_resultado_edital):
        get_resultado_edital.return_value = mock.Mock()
        get_resultado_edital.return_value.is_final.return_value = True
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertTrue(inscricao.is_resultado_final)

    @mock.patch('psct.models.Inscricao.get_resultado_edital')
    def test_is_resultado_final_deve_retornar_falso_quando_nao_ha_resultado_edital(
            self, get_resultado_edital
    ):
        get_resultado_edital.return_value = None
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertFalse(inscricao.is_resultado_final)

    @mock.patch('psct.models.Inscricao.get_resultado_edital')
    def test_is_resultado_final_deve_retornar_falso_quando_resultado_edital_nao_eh_final(
            self, get_resultado_edital
    ):
        get_resultado_edital.return_value = mock.Mock()
        get_resultado_edital.return_value.is_final.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertFalse(inscricao.is_resultado_final)

    @freeze_time(datetime.datetime.now())
    def test_pode_ver_resultado_preliminar_deve_retornar_verdadeiro(self):
        data_resultado_preliminar = datetime.datetime.now() - datetime.timedelta(minutes=10)
        processo_inscricao = recipes.processo_inscricao.make(
            data_resultado_preliminar=data_resultado_preliminar
        )
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.assertTrue(inscricao.pode_ver_resultado_preliminar)

    @freeze_time(datetime.datetime.now())
    def test_pode_ver_resultado_preliminar_deve_retornar_falso_se_data_resultado_igual_agora(
            self
    ):
        data_resultado_preliminar = datetime.datetime.now()
        processo_inscricao = recipes.processo_inscricao.make(
            data_resultado_preliminar=data_resultado_preliminar
        )
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.assertFalse(inscricao.pode_ver_resultado_preliminar)

    @freeze_time(datetime.datetime.now())
    def test_pode_ver_resultado_preliminar_deve_retornar_falso_se_data_resultado_maior_que_agora(
            self
    ):
        data_resultado_preliminar = datetime.datetime.now() + datetime.timedelta(minutes=10)
        processo_inscricao = recipes.processo_inscricao.make(
            data_resultado_preliminar=data_resultado_preliminar
        )
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.assertFalse(inscricao.pode_ver_resultado_preliminar)

    def test_get_anos_requeridos_deve_retornar_anos_escolares_do_fundamental(self):
        inscricao = recipes.inscricao.make(
            edital=self.edital, curso__formacao=Formacao.INTEGRADO.name
        )
        self.assertListEqual([6, 7, 8], inscricao.get_anos_requeridos())

    def test_get_anos_requeridos_deve_retornar_anos_escolares_do_ensino_medio(self):
        inscricao = recipes.inscricao.make(
            edital=self.edital, curso__formacao=Formacao.SUBSEQUENTE.name
        )
        self.assertListEqual([1, 2], inscricao.get_anos_requeridos())

    def test_get_anos_requeridos_deve_lancar_erro_por_formacao_errada(self):
        inscricao = recipes.inscricao.make(
            edital=self.edital, curso__formacao=Formacao.MESTRADO.name
        )
        with self.assertRaises(ValueError) as ex:
            inscricao.get_anos_requeridos()
        self.assertEqual("Formação errada", ex.exception.args[0])

    def test_is_owner_deve_retornar_verdadeiro(self):
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertTrue(inscricao.is_owner(inscricao.candidato.user))

    def test_is_owner_deve_retornar_falso(self):
        user = base.tests.recipes.user.make()
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertFalse(inscricao.is_owner(user))

    def test_pode_inserir_notas_deve_retornar_verdadeiro(self):
        processo_inscricao = recipes.processo_inscricao.make(
            formacao=Formacao.SUBSEQUENTE.name
        )
        inscricao = recipes.inscricao.make(
            edital=processo_inscricao.edital,
            curso__formacao=processo_inscricao.formacao,
        )
        if hasattr(inscricao, "pontuacao"):
            pontuacao = inscricao.pontuacao
        else:
            pontuacao = recipes.pontuacao_inscricao.make(inscricao=inscricao)
        recipes.nota_anual.make(pontuacao=pontuacao)
        self.assertTrue(inscricao.pode_inserir_notas())

    @mock.patch('psct.models.Inscricao.pode_alterar', new_callable=mock.PropertyMock)
    def test_pode_inserir_comprovantes_deve_retornar_verdadeiro_se_existe_comprovante(
            self, pode_alterar
    ):
        pode_alterar.return_value = True
        inscricao = recipes.inscricao.make(edital=self.edital)
        recipes.comprovante.make(inscricao=inscricao)
        self.assertTrue(inscricao.pode_inserir_comprovantes())

    @mock.patch('psct.models.Inscricao.pode_alterar', new_callable=mock.PropertyMock)
    def test_pode_inserir_comprovantes_deve_retornar_verdadeiro_se_existe_nota(
            self, pode_alterar
    ):
        pode_alterar.return_value = True
        processo_inscricao = recipes.processo_inscricao.make(formacao=Formacao.SUBSEQUENTE.name)
        inscricao = recipes.inscricao.make(
            edital=processo_inscricao.edital,
            curso__formacao=processo_inscricao.formacao,
        )
        if hasattr(inscricao, "pontuacao"):
            pontuacao = inscricao.pontuacao
        else:
            pontuacao = recipes.pontuacao_inscricao.make(inscricao=inscricao)
        recipes.nota_anual.make(portugues=1, pontuacao=pontuacao)
        self.assertTrue(inscricao.pode_inserir_comprovantes())

    @mock.patch('psct.models.Inscricao.pode_alterar', new_callable=mock.PropertyMock)
    def test_pode_inserir_comprovantes_deve_retornar_falso_se_inscricao_nao_pode_alterar(
            self, pode_alterar
    ):
        pode_alterar.return_value = False
        processo_inscricao = recipes.processo_inscricao.make()
        inscricao = recipes.inscricao.make(
            edital=processo_inscricao.edital,
            curso__formacao=processo_inscricao.formacao,
        )
        recipes.comprovante.make(inscricao=inscricao)
        if hasattr(inscricao, "pontuacao"):
            pontuacao = inscricao.pontuacao
        else:
            pontuacao = recipes.pontuacao_inscricao.make(inscricao=inscricao)
        recipes.nota_anual.make(pontuacao=pontuacao)
        self.assertFalse(inscricao.pode_inserir_comprovantes())

    @mock.patch('psct.models.Inscricao.pode_alterar', new_callable=mock.PropertyMock)
    def test_pode_inserir_comprovantes_deve_retornar_falso_quando_nao_existe_comprovante_ou_nota(
            self, pode_alterar
    ):
        pode_alterar.return_value = True
        processo_inscricao = recipes.processo_inscricao.make()
        inscricao = recipes.inscricao.make(
            edital=processo_inscricao.edital,
            curso__formacao=processo_inscricao.formacao,
        )
        if hasattr(inscricao, "pontuacao"):
            pontuacao = inscricao.pontuacao
        else:
            pontuacao = recipes.pontuacao_inscricao.make(inscricao=inscricao)
        recipes.nota_anual.make(portugues=0, pontuacao=pontuacao)
        self.assertFalse(inscricao.pode_inserir_comprovantes())

    @mock.patch('psct.models.Inscricao.is_concluida', new_callable=mock.PropertyMock)
    def test_pode_visualizar_inscricao_deve_retornar_verdadeiro_se_inscricao_estiver_concluida(
            self, is_concluida
    ):
        is_concluida.return_value = True
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=True)
        self.assertTrue(inscricao.pode_visualizar_inscricao())

    @mock.patch('psct.models.Inscricao.is_concluida', new_callable=mock.PropertyMock)
    def test_pode_visualizar_inscricao_deve_retornar_falso_se_inscricao_nao_estiver_concluida(
            self, is_concluida
    ):
        is_concluida.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=True)
        self.assertFalse(inscricao.pode_visualizar_inscricao())

    @mock.patch('psct.models.Inscricao.is_cancelada', new_callable=mock.PropertyMock)
    @mock.patch('psct.models.Inscricao.is_selecao_curso_tecnico', new_callable=mock.PropertyMock)
    def test_is_concluida_deve_retornar_verdade_se_inscricao_estiver_aceita_e_nao_cancelada(
            self, is_selecao_curso_tecnico, is_cancelada
    ):
        is_selecao_curso_tecnico.return_value = False
        is_cancelada.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=True)
        self.assertTrue(inscricao.is_concluida)

    @mock.patch('psct.models.Inscricao.is_cancelada', new_callable=mock.PropertyMock)
    @mock.patch('psct.models.Inscricao.is_selecao_curso_tecnico', new_callable=mock.PropertyMock)
    def test_is_concluida_deve_retornar_verdadeiro_para_cursos_tecnicos(
            self, is_selecao_curso_tecnico, is_cancelada
    ):
        is_selecao_curso_tecnico.return_value = True
        is_cancelada.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=True)
        recipes.comprovante.make(inscricao=inscricao)
        self.assertTrue(inscricao.is_concluida)

    @mock.patch('psct.models.Inscricao.is_cancelada', new_callable=mock.PropertyMock)
    @mock.patch('psct.models.Inscricao.is_selecao_curso_tecnico', new_callable=mock.PropertyMock)
    def test_is_concluida_deve_retornar_falso_para_inscricao_de_tecnico_sem_comprovantes(
            self, is_selecao_curso_tecnico, is_cancelada
    ):
        is_selecao_curso_tecnico.return_value = True
        is_cancelada.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=True)
        self.assertFalse(inscricao.is_concluida)

    @mock.patch('psct.models.Inscricao.is_cancelada', new_callable=mock.PropertyMock)
    @mock.patch('psct.models.Inscricao.is_selecao_curso_tecnico', new_callable=mock.PropertyMock)
    def test_is_concluida_deve_retornar_falso_quando_nao_ha_aceite_marcado(
            self, is_selecao_curso_tecnico, is_cancelada
    ):
        is_selecao_curso_tecnico.return_value = False
        is_cancelada.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=False)
        self.assertFalse(inscricao.is_concluida)

    @mock.patch('psct.models.Inscricao.is_cancelada', new_callable=mock.PropertyMock)
    @mock.patch('psct.models.Inscricao.is_selecao_curso_tecnico', new_callable=mock.PropertyMock)
    def test_is_concluida_deve_retornar_falso_quando_inscricao_esta_cancelada(
            self, is_selecao_curso_tecnico, is_cancelada
    ):
        is_selecao_curso_tecnico.return_value = False
        is_cancelada.return_value = True
        inscricao = recipes.inscricao.make(edital=self.edital, aceite=True)
        self.assertFalse(inscricao.is_concluida)

    def test_has_resultado_deve_retornar_verdade_se_edital_tem_resultado_preliminar(self):
        recipes.resultado_preliminar_homologado.make(edital=self.edital)
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertTrue(inscricao.has_resultado)

    def test_has_resultado_deve_retornar_verdade_se_edital_tem_resultado_final(self):
        inscricao = recipes.inscricao.make(edital=self.edital)
        recipes.resultado_final.make(edital=self.edital)
        self.assertTrue(inscricao.has_resultado)

    def test_has_resultado_deve_retornar_falso_nao_foi_gerado_resultado(self):
        processo_inscricao = recipes.processo_inscricao.make()
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.assertFalse(inscricao.has_resultado)

    @mock.patch("psct.models.Inscricao.is_cancelada", new_callable=mock.PropertyMock)
    def test_get_situacao_deve_retonar_inscricao_cancelada(self, is_cancelada):
        is_cancelada.return_value = True
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertIsInstance(inscricao.get_situacao(), models.SituacaoInscricaoCancelada)

    @mock.patch("psct.models.Inscricao.get_resultado_edital")
    @mock.patch("psct.models.Inscricao.get_situacao_resultado")
    @mock.patch("psct.models.ProcessoInscricao.em_periodo_inscricao", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.has_resultado", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.pode_ver_resultado_preliminar", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.is_concluida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.is_cancelada", new_callable=mock.PropertyMock)
    def test_get_situacao_deve_retonar_situacao_resultado_apos_a_data_do_resultado(
            self, is_cancelada, is_concluida, pode_ver_resultado_preliminar,
            has_resultado, em_periodo_inscricao, get_situacao_resultado, get_resultado_edital
    ):
        is_cancelada.return_value = False
        is_concluida.return_value = True
        pode_ver_resultado_preliminar.return_value = True
        has_resultado.return_value = True
        em_periodo_inscricao.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertEqual(get_situacao_resultado.return_value, inscricao.get_situacao())

    @mock.patch("psct.models.ProcessoInscricao.em_periodo_inscricao", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.has_resultado", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.pode_ver_resultado_preliminar", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.is_concluida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.is_cancelada", new_callable=mock.PropertyMock)
    def test_get_situacao_deve_retonar_aguardando_se_nao_tiver_um_resultado_apos_o_prazo(
            self, is_cancelada, is_concluida, pode_ver_resultado_preliminar,
            has_resultado, em_periodo_inscricao
    ):
        is_cancelada.return_value = False
        is_concluida.return_value = True
        pode_ver_resultado_preliminar.return_value = True
        has_resultado.return_value = False
        em_periodo_inscricao.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertIsInstance(inscricao.get_situacao(), models.SituacaoAguardandoResultado)

    @mock.patch("psct.models.ProcessoInscricao.em_periodo_inscricao", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.has_resultado", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.pode_ver_resultado_preliminar", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.is_concluida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.is_cancelada", new_callable=mock.PropertyMock)
    def test_get_situacao_deve_retonar_aguardando_entre_o_final_da_inscricao_e_data_do_resultado(
            self, is_cancelada, is_concluida, pode_ver_resultado_preliminar,
            has_resultado, em_periodo_inscricao
    ):
        is_cancelada.return_value = False
        is_concluida.return_value = True
        pode_ver_resultado_preliminar.return_value = False
        has_resultado.return_value = True
        em_periodo_inscricao.return_value = False
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertIsInstance(inscricao.get_situacao(), models.SituacaoAguardandoResultado)

    @mock.patch("psct.models.ProcessoInscricao.em_periodo_inscricao", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.has_resultado", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.pode_ver_resultado_preliminar", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.is_concluida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.is_cancelada", new_callable=mock.PropertyMock)
    def test_get_situacao_deve_retonar_inscricao_nao_concluida_em_periodo_de_inscricao(
            self, is_cancelada, is_concluida, pode_ver_resultado_preliminar,
            has_resultado, em_periodo_inscricao
    ):
        is_cancelada.return_value = False
        is_concluida.return_value = False
        pode_ver_resultado_preliminar.return_value = False
        has_resultado.return_value = False
        em_periodo_inscricao.return_value = True
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertIsInstance(inscricao.get_situacao(), models.SituacaoInscricaoNaoConcluida)

    @mock.patch("psct.models.ProcessoInscricao.em_periodo_inscricao", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.has_resultado", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.pode_ver_resultado_preliminar", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.is_concluida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.Inscricao.is_cancelada", new_callable=mock.PropertyMock)
    def test_get_situacao_deve_retonar_valor_vazio_se_inscricao_concluida_e_periodo_de_inscricao(
            self, is_cancelada, is_concluida, pode_ver_resultado_preliminar,
            has_resultado, em_periodo_inscricao
    ):
        is_cancelada.return_value = False
        is_concluida.return_value = True
        pode_ver_resultado_preliminar.return_value = False
        has_resultado.return_value = False
        em_periodo_inscricao.return_value = True
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertIsNone(inscricao.get_situacao())

    @mock.patch("psct.models.Inscricao.em_periodo_inscricao", new_callable=mock.PropertyMock)
    def test_clean_deve_validar_se_estar_em_periodo_de_inscricao(self, em_periodo_inscricao):
        em_periodo_inscricao.return_value = False
        processo_inscricao = recipes.processo_inscricao.make()
        with self.assertRaises(ValidationError) as ex:
            models.Inscricao(edital=processo_inscricao.edital).clean()
        self.assertEqual("Impossível alterar objeto", ex.exception.args[0])

    def test_clean_deve_validar_preenchimento_indevido_de_segunda_opcao(self):
        processo_inscricao = recipes.processo_inscricao.make(possui_segunda_opcao=False)
        curso = recipes.curso_selecao.make()
        inscricao = recipes.inscricao.prepare(
            edital=processo_inscricao.edital,
            curso_segunda_opcao=curso
        )
        with self.assertRaises(ValidationError) as cm:
            inscricao.clean()
        self.assertIn(
            "Não é permitido selecionar uma segunda opção de curso.",
            cm.exception.message_dict.get("com_segunda_opcao"),
        )

    def test_clean_nao_deve_validar_quando_segunda_opcao_nao_preenchido(self):
        processo_inscricao = recipes.processo_inscricao.make(possui_segunda_opcao=False)
        inscricao = recipes.inscricao.prepare(
            edital=processo_inscricao.edital,
            curso_segunda_opcao=None,
        )
        self.assertIsNone(inscricao.clean())

    def test_get_absolute_url_deve_estar_corretamente_configurada(self):
        inscricao = recipes.inscricao.make(edital=self.edital)
        self.assertEqual(
            reverse("visualizar_inscricao_psct", kwargs={"pk": inscricao.id}),
            inscricao.get_absolute_url()
        )


class BoxCursoTestCase(DiretorEnsinoPermissionData, TestCase):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]

    def test_deveria_retornar_informacoes_do_curso_sem_cota(self):
        curso_selecao = cursos.recipes.curso_selecao.make()
        ampla = models.Modalidade.objects.get(equivalente_id=ModalidadeEnum.ampla_concorrencia)
        processo_inscricao = recipes.processo_inscricao.make()
        inscricao = recipes.inscricao.make(modalidade_cota=ampla, edital=processo_inscricao.edital)
        expected = [
            ["<b>Campus:</b>", f"{curso_selecao.campus}"],
            ["<b>Tipo de Formação:</b>", f"{curso_selecao.get_formacao_display()}"],
            ["<b>Curso:</b>", f"{curso_selecao.curso.nome}"],
            ["<b>Turno:</b>", f"{curso_selecao.get_turno_display()}"],
            ["<b>Modalidade de Cota:</b>", "Nenhuma"],
        ]
        self.assertEqual(expected, pdf._create_box_curso(curso_selecao, inscricao))

    def test_deveria_retornar_informacoes_do_curso_com_cota(self):
        curso_selecao = cursos.recipes.curso_selecao.make()
        pcd = models.Modalidade.objects.get(equivalente_id=ModalidadeEnum.deficientes)
        processo_inscricao = recipes.processo_inscricao.make()
        inscricao = recipes.inscricao.make(modalidade_cota=pcd, edital=processo_inscricao.edital)
        expected = [
            ["<b>Campus:</b>", f"{curso_selecao.campus}"],
            ["<b>Tipo de Formação:</b>", f"{curso_selecao.get_formacao_display()}"],
            ["<b>Curso:</b>", f"{curso_selecao.curso.nome}"],
            ["<b>Turno:</b>", f"{curso_selecao.get_turno_display()}"],
            ["<b>Modalidade de Cota:</b>", str(pcd)],
        ]
        self.assertEqual(expected, pdf._create_box_curso(curso_selecao, inscricao))

    def test_deveria_retornar_informacoes_do_curso_com_polo(self):
        polo = cursos.recipes.polo.make()
        curso_selecao = cursos.recipes.curso_selecao.make(polo=polo)
        pcd = models.Modalidade.objects.get(equivalente_id=ModalidadeEnum.deficientes)
        processo_inscricao = recipes.processo_inscricao.make()
        inscricao = recipes.inscricao.make(modalidade_cota=pcd, edital=processo_inscricao.edital)
        expected = [
            ["<b>Campus:</b>", f"{curso_selecao.campus}"],
            ["<b>Polo:</b>", f"{str(polo)}"],
            ["<b>Tipo de Formação:</b>", f"{curso_selecao.get_formacao_display()}"],
            ["<b>Curso:</b>", f"{curso_selecao.curso.nome}"],
            ["<b>Turno:</b>", f"{curso_selecao.get_turno_display()}"],
            ["<b>Modalidade de Cota:</b>", str(pcd)],
        ]
        self.assertEqual(expected, pdf._create_box_curso(curso_selecao, inscricao))


class BoxPontuacaoTestCase(DiretorEnsinoPermissionData, TestCase):

    def test_deveria_retornar_informacoes_da_pontuacao_com_historia_e_geografia(self):
        processo = recipes.processo_inscricao.make(formacao=models.ProcessoInscricao.INTEGRADO)
        inscricao = recipes.inscricao.make(edital=processo.edital)
        expected = [
            ["<b>Pontuação Total:</b>", f"{inscricao.pontuacao.valor}"],
            ["<b>Pontuação em Português:</b>", f"{inscricao.pontuacao.valor_pt}"],
            ["<b>Pontuação em Matemática:</b>", f"{inscricao.pontuacao.valor_mt}"],
            [
                "<b>Pontuação em História:</b>",
                f"{inscricao.pontuacao.get_pontuacao_historia_display()}",
            ],
            [
                "<b>Pontuação em Geografia:</b>",
                f"{inscricao.pontuacao.get_pontuacao_geografia_display()}",
            ],
        ]
        self.assertEqual(expected, pdf._create_box_pontuacao(inscricao.pontuacao))

    def test_deveria_retornar_informacoes_da_pontuacao_sem_historia_e_geografia(self):
        curso = recipes.curso_psct.make(formacao=Formacao.SUBSEQUENTE.name)
        processo = recipes.processo_inscricao.make(formacao=models.ProcessoInscricao.INTEGRADO)
        inscricao = recipes.inscricao.make(edital=processo.edital, curso=curso)
        expected = [
            ["<b>Pontuação Total:</b>", f"{inscricao.pontuacao.valor}"],
            ["<b>Pontuação em Português:</b>", f"{inscricao.pontuacao.valor_pt}"],
            ["<b>Pontuação em Matemática:</b>", f"{inscricao.pontuacao.valor_mt}"],
        ]
        self.assertEqual(expected, pdf._create_box_pontuacao(inscricao.pontuacao))
