from datetime import datetime
from decimal import Decimal

from django.test import TestCase
from freezegun import freeze_time
from model_mommy import mommy

import base.tests.recipes
from cursos.tests.mixins import DiretorEnsinoPermissionData
from . import recipes
from .. import loaders
from .. import models


class SafeDecimalTestCase(TestCase):
    def test_deveria_trocar_virgula_por_ponto(self):
        self.assertEqual(loaders.safe_decimal("15,60"), Decimal("15.60"))

    def test_deveria_manter_ponto(self):
        self.assertEqual(loaders.safe_decimal("15.60"), Decimal("15.60"))


class ModalidadeSisuLoaderTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.loader = loaders.ModalidadeSisuLoader(context={}, line=[])

    def test_context_name_deveria_estar_configurado_corretamente(self):
        self.assertEqual("modalidade", self.loader.context_name)

    def test_unique_attrs_deveria_estar_configurado_corretamente(self):
        self.assertEqual(["nome"], self.loader.unique_attrs)

    def test_fields_deveria_estar_configurado_corretamente(self):
        self.assertEqual(1, len(self.loader.fields))
        self.assertEqual("NO_MODALIDADE_CONCORRENCIA", self.loader.fields[0].column)
        self.assertEqual("nome", self.loader.fields[0].target_attribute)

    def test_nao_deveria_criar_modalidade(self):
        with self.assertRaises(ValueError) as ex:
            self.loader.create_object([])

        self.assertEqual("Não pode criar novas modalidades", ex.exception.args[0])

    def test_deveria_retornar_modalidade(self):
        modalidade_variavel = recipes.modalidade_variavel.make()
        self.assertEqual(
            modalidade_variavel.modalidade,
            self.loader.get_object(key={"nome": "Modalidade variável 1"}),
        )

    def test_deveria_retornar_none(self):
        recipes.modalidade_variavel.make()
        self.assertIsNone(self.loader.get_object(key={"nome": "Modalidade variável 2"}))


class InscricaoSisuLoaderTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.loader = loaders.InscricaoSisuLoader(context={}, line=[])

    def test_context_name_deveria_estar_configurado_corretamente(self):
        self.assertEqual("inscricao", self.loader.context_name)

    def test_context_requires_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            ("edicao", "modalidade", "candidato"), self.loader.context_requires
        )

    def test_unique_attrs_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            ("edicao", "modalidade", "candidato", "curso"), self.loader.unique_attrs
        )

    def test_deveriar_haver_dois_fields(self):
        self.assertEqual(2, len(self.loader.fields))

    def test_deveria_haver_turno_em_fields(self):
        self.assertEqual("DS_TURNO", self.loader.fields[0].column)
        self.assertEqual("turno", self.loader.fields[0].target_attribute)

    def test_deveria_haver_curso_em_fields(self):
        self.assertEqual("CO_IES_CURSO", self.loader.fields[1].column)
        self.assertEqual("codigo", self.loader.fields[1].target_attribute)

    def test_get_data_deveria_retornar_curso(self):
        curso = mommy.make("cursos.CursoSelecao", codigo=13, turno="DIURNO")
        inscricao = recipes.inscricao.make()
        loader = loaders.InscricaoSisuLoader(
            context={
                "edicao": inscricao.edicao,
                "modalidade": inscricao.chamada.modalidade,
                "candidato": inscricao.candidato,
            },
            line={"DS_TURNO": "Diurno", "CO_IES_CURSO": "13"},
        )
        self.assertEqual(curso, loader.get_data()["curso"])


class CandidatoSisuLoaderTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.loader = loaders.CandidatoSisuLoader(context={}, line=[])

    def test_context_name_deveria_estar_configurado_corretamente(self):
        self.assertEqual("candidato", self.loader.context_name)

    def test_unique_attrs_deveria_estar_configurado_corretamente(self):
        self.assertEqual(["cpf"], self.loader.unique_attrs)

    def test_deveriar_haver_quinze_fields(self):
        self.assertEqual(15, len(self.loader.fields))

    def test_deveria_haver_cpf_em_fields(self):
        self.assertEqual("NU_CPF_INSCRITO", self.loader.fields[0].column)
        self.assertEqual("cpf", self.loader.fields[0].target_attribute)

    def test_deveria_haver_rg_em_fields(self):
        self.assertEqual("NU_RG", self.loader.fields[1].column)
        self.assertEqual("rg", self.loader.fields[1].target_attribute)

    def test_deveria_haver_nome_em_fields(self):
        self.assertEqual("NO_INSCRITO", self.loader.fields[2].column)
        self.assertEqual("nome", self.loader.fields[2].target_attribute)

    def test_deveria_haver_data_nascimento_em_fields(self):
        self.assertEqual("DT_NASCIMENTO", self.loader.fields[3].column)
        self.assertEqual("nascimento", self.loader.fields[3].target_attribute)

    def test_deveria_haver_nome_mae_em_fields(self):
        self.assertEqual("NO_MAE", self.loader.fields[4].column)
        self.assertEqual("nome_mae", self.loader.fields[4].target_attribute)

    def test_deveria_haver_logradouro_em_fields(self):
        self.assertEqual("DS_LOGRADOURO", self.loader.fields[5].column)
        self.assertEqual("logradouro", self.loader.fields[5].target_attribute)

    def test_deveria_haver_endereco_em_fields(self):
        self.assertEqual("NU_ENDERECO", self.loader.fields[6].column)
        self.assertEqual("numero_endereco", self.loader.fields[6].target_attribute)

    def test_deveria_haver_complemento_do_endereco_em_fields(self):
        self.assertEqual("DS_COMPLEMENTO", self.loader.fields[7].column)
        self.assertEqual("complemento_endereco", self.loader.fields[7].target_attribute)

    def test_deveria_haver_uf_em_fields(self):
        self.assertEqual("SG_UF_INSCRITO", self.loader.fields[8].column)
        self.assertEqual("uf", self.loader.fields[8].target_attribute)

    def test_deveria_haver_municipio_em_fields(self):
        self.assertEqual("NO_MUNICIPIO", self.loader.fields[9].column)
        self.assertEqual("municipio", self.loader.fields[9].target_attribute)

    def test_deveria_haver_bairro_em_fields(self):
        self.assertEqual("NO_BAIRRO", self.loader.fields[10].column)
        self.assertEqual("bairro", self.loader.fields[10].target_attribute)

    def test_deveria_haver_cep_em_fields(self):
        self.assertEqual("NU_CEP", self.loader.fields[11].column)
        self.assertEqual("cep", self.loader.fields[11].target_attribute)

    def test_deveria_haver_fone1_em_fields(self):
        self.assertEqual("NU_FONE1", self.loader.fields[12].column)
        self.assertEqual("telefone2", self.loader.fields[12].target_attribute)

    def test_deveria_haver_fone2_em_fields(self):
        self.assertEqual("NU_FONE2", self.loader.fields[13].column)
        self.assertEqual("telefone", self.loader.fields[13].target_attribute)

    def test_deveria_haver_email_em_fields(self):
        self.assertEqual("DS_EMAIL", self.loader.fields[14].column)
        self.assertEqual("email", self.loader.fields[14].target_attribute)

    def test_clean_nome_deveria_retornar_letrar_maiusculas(self):
        self.assertEqual("JOSÉ FRANCA", self.loader.clean_nome("José Franca"))

    @freeze_time("2020-09-11 15:00:00")
    def test_clean_data_nascimento(self):
        self.assertEqual(
            datetime.now(), self.loader.clean_nascimento("2020-09-11 15:00:00")
        )

    def test_clean_cpf_deveriar_retornar_com_pontuacao(self):
        self.assertEqual("111.111.111-11", self.loader.clean_cpf("11111111111"))

    def test_clean_bairro_deveria_retornar_bairro_sem_alteracao(self):
        self.assertEqual("bancários", self.loader.clean_bairro("bancários"))

    def test_clean_bairro_deveria_retornar_string_vazia(self):
        self.assertEqual("", self.loader.clean_bairro("-----"))

    def test_clean_cep_com_pontuacao(self):
        self.assertEqual("11.111-111", self.loader.clean_cep("11111111"))

    def test_clean_telefone_de_tamanho_pequeno_deveria_retornar_none(self):
        self.assertIsNone(self.loader.clean_telefone("11111111"))

    def test_clean_telefone_com_pontuacao_nao_deveria_sofrer_alteracao(self):
        self.assertEqual("1111-1111", self.loader.clean_telefone("1111-1111"))

    def test_get_object_deveria_retornar_none(self):
        self.assertIsNone(self.loader.get_object({"cpf": "111.111.111-11"}))

    def test_get_object_deveria_retornar_candidato(self):
        candidato = recipes.candidato.make()
        self.assertEqual(
            candidato, self.loader.get_object({"cpf": candidato.pessoa.cpf})
        )

    def test_create_object_deveria_retornar_candidato_existente(self):
        candidato = recipes.candidato.make()
        self.assertEqual(
            candidato, self.loader.create_object({"cpf": candidato.pessoa.cpf})
        )

    def test_create_object_deveria_criar_novo_candidato(self):
        pessoa = base.tests.recipes.pessoa_fisica.make()
        self.loader.create_object({"cpf": pessoa.cpf})
        self.assertTrue(models.Candidato.objects.filter(pessoa=pessoa).exists())


class DesempenhoSisuLoaderTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.loader = loaders.DesempenhoSisuLoader(context={}, line=[])

    def test_context_name_deveria_estar_configurado_corretamente(self):
        self.assertEqual("desempenho", self.loader.context_name)

    def test_context_requires_deveria_estar_configurado_corretamente(self):
        self.assertEqual(("inscricao",), self.loader.context_requires)

    def test_unique_attrs_deveria_estar_configurado_corretamente(self):
        self.assertEqual(("inscricao",), self.loader.unique_attrs)

    def test_deveriar_haver_quinze_fields(self):
        self.assertEqual(7, len(self.loader.fields))

    def test_deveria_haver_cpf_em_fields(self):
        self.assertEqual("NU_NOTA_L", self.loader.fields[0].column)
        self.assertEqual("nota_em_linguas", self.loader.fields[0].target_attribute)

    def test_deveria_haver_rg_em_fields(self):
        self.assertEqual("NU_NOTA_CH", self.loader.fields[1].column)
        self.assertEqual("nota_em_humanas", self.loader.fields[1].target_attribute)

    def test_deveria_haver_nome_em_fields(self):
        self.assertEqual("NU_NOTA_CN", self.loader.fields[2].column)
        self.assertEqual(
            "nota_em_ciencias_naturais", self.loader.fields[2].target_attribute
        )

    def test_deveria_haver_data_nascimento_em_fields(self):
        self.assertEqual("NU_NOTA_M", self.loader.fields[3].column)
        self.assertEqual("nota_em_matematica", self.loader.fields[3].target_attribute)

    def test_deveria_haver_nome_mae_em_fields(self):
        self.assertEqual("NU_NOTA_R", self.loader.fields[4].column)
        self.assertEqual("nota_na_redacao", self.loader.fields[4].target_attribute)

    def test_deveria_haver_logradouro_em_fields(self):
        self.assertEqual("NU_NOTA_CANDIDATO", self.loader.fields[5].column)
        self.assertEqual("nota_geral", self.loader.fields[5].target_attribute)

    def test_deveria_haver_classificacao_em_fields(self):
        self.assertEqual("NU_CLASSIFICACAO", self.loader.fields[6].column)
        self.assertEqual("classificacao", self.loader.fields[6].target_attribute)
