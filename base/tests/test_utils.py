import datetime
from unittest import mock

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.test import TestCase

from .. import utils
from .. import choices

import base.custom.utils

class GetSrcMapaTestCase(TestCase):

    def test_deveria_retornar_vazio_para_qualquer_valor_que_nao_seja_html(self):
        self.assertEqual("", utils.get_src_mapa(""))

    def test_deveria_retornar_o_conteudo_do_atributo_src_do_iframe(self):
        html = '<iframe src="valor_esperado"></iframe>'
        self.assertEqual("valor_esperado", utils.get_src_mapa(html))


class JoinByTestCase(TestCase):
    def test_deveria_colocar_separador_nos_itens_da_lista(self):
        self.assertEqual("a,b", utils.join_by(["a", "b"], ","))


class HumanListTestCase(TestCase):
    def test_lista_vazia_retorna_string_vazia(self):
        self.assertEqual("", utils.human_list([]))

    def test_lista_com_um_unico_elemento_nao_tem_separador(self):
        self.assertEqual("Palavra", utils.human_list(["Palavra"]))

    def test_lista_com_dois_elementos_nao_tem_ultimo_separador_padrao_letra_e(self):
        self.assertEqual("a e b", utils.human_list(["a", "b"]))

    def test_lista_com_dois_elementos_nao_tem_ultimo_separador_definido(self):
        self.assertEqual("a sep b", utils.human_list(["a", "b"], last_separator=" sep "))

    def test_lista_com_tres_elementos_tem_separador_padrao_virgula(self):
        self.assertEqual("a, b e c", utils.human_list(["a", "b", "c"]))

    def test_lista_com_tres_elementos_tem_separador_definido(self):
        self.assertEqual("a! b e c", utils.human_list(["a", "b", "c"], separator="! "))

    def test_lista_com_tres_elementos_tem_separador_definido_e_ultimo_separador_definifo(self):
        self.assertEqual(
            "a! b # c", utils.human_list(["a", "b", "c"], separator="! ", last_separator=" # ")
        )


class DiasEntreTestCase(TestCase):

    def test_deveria_ser_zero_quando_inicio_for_igual_fim(self):
        self.assertEqual(0, utils.dias_entre(datetime.date.today(), datetime.date.today()))

    def test_deveria_ser_um_quando_inicio_foi_onte_e_o_fim_hoje(self):
        self.assertEqual(
            1,
            utils.dias_entre(
                datetime.date.today() - datetime.timedelta(days=1),
                datetime.date.today()
            )
        )

    def test_deveria_ser_um_negativo_quando_inicio_eh_amanha_e_o_fim_hoje(self):
        self.assertEqual(
            -1,
            utils.dias_entre(
                datetime.date.today() + datetime.timedelta(days=1),
                datetime.date.today()
            )
        )

    def test_deveria_lancar_excecao_se_inicio_for_vazio(self):
        with self.assertRaises(ValidationError):
            utils.dias_entre(None, datetime.date.today())

    def test_deveria_lancar_excecao_se_fim_for_vazio(self):
        with self.assertRaises(ValidationError):
            utils.dias_entre(datetime.date.today(), None)

    def test_deveria_calcular_corretamente_se_inicio_for_datetime(self):
        self.assertEqual(0, utils.dias_entre(datetime.datetime.now(), datetime.date.today()))

    def test_deveria_calcular_corretamente_se_fim_for_datetime(self):
        self.assertEqual(0, utils.dias_entre(datetime.date.today(), datetime.datetime.now()))


class CPFTestCase(TestCase):

    def test_deveria_definir_numeros_no_atributo_cpf(self):
        cpf = utils.CPF("1" * 11)
        self.assertEqual("1" * 11, cpf.cpf)

    def test_deveria_lancar_excecao_se_nao_houver_todos_os_numeros(self):
        with self.assertRaises(ValidationError):
            utils.CPF(["1" * 10])

    def test_deveria_lancar_excecao_se_houver_numeros_a_mais(self):
        with self.assertRaises(ValidationError):
            utils.CPF("1" * 12)

    def test_deveria_transformar_lista_de_numeros_em_string_unica(self):
        cpf = utils.CPF([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        self.assertEqual("1" * 11, cpf.cpf)

    def test_deveria_remover_caracteres_ponto_e_traco_do_numero(self):
        cpf = utils.CPF("111.111.111-11")
        self.assertEqual("11111111111", cpf.cpf)

    def test_deveria_lancar_excecao_se_ha_caracteres_nao_esperado_no_numero(self):
        with self.assertRaises(ValidationError):
            utils.CPF([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, "a"])

        with self.assertRaises(ValidationError):
            utils.CPF([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, "*"])

        with self.assertRaises(ValidationError):
            utils.CPF([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, "^"])

    def test_format_number_deveria_adicionar_pontos_e_traco_no_numero(self):
        self.assertEqual("111.111.111-11", utils.CPF.format_number("11111111111"))

    def test_format_deveria_adicionar_pontos_e_traco_no_numero(self):
        self.assertEqual("111.111.111-11", utils.CPF("11111111111").format())

    def test_numero_deveria_ser_valido(self):
        self.assertTrue(utils.CPF("675.944.763-87").valido())

    def test_numero_deveria_ser_invalido(self):
        self.assertFalse(utils.CPF("675.944.763-80").valido())

    def test_validate_number_deveria_ser_valido(self):
        self.assertTrue(utils.CPF.validate_number("67594476387"))

    def test_validate_number_deveria_ser_invalido_para_numeros_repetidos(self):
        invalidos = [11 * str(i) for i in range(10)]
        for invalido in invalidos:
            self.assertFalse(utils.CPF.validate_number(invalido))

    def test_deveria_ser_igual(self):
        self.assertTrue("1" * 11 == utils.CPF("1" * 11))

    def test_deveria_ser_diferente(self):
        self.assertFalse("2" * 11 == utils.CPF("1" * 11))

    def test_avaliacao_booleana_deveria_ser_valido(self):
        self.assertTrue(bool(utils.CPF("675.944.763-87")))

    def test_str_deveria_retornar_o_numero_formatado(self):
        self.assertEqual("675.944.763-87", str(utils.CPF("67594476387")))

    def test_repr_deveria_numero_com_nome_da_classe(self):
        self.assertEqual("CPF('67594476387')", repr(utils.CPF("67594476387")))

    def test_getitem_deveria_numero_da_posicao_correspondente(self):
        self.assertEqual("7", utils.CPF("67594476387")[1])

    def test_deveria_ser_diferente_para_numero_invalido(self):
        self.assertTrue("2" * 10 != utils.CPF("1" * 11))


class FileExtensionTestCase(TestCase):
    def test_deveria_retornar_a_extensao_do_arquivo(self):
        file = mock.Mock()
        file.name = "/path/to/file.txt"
        self.assertEqual(".txt", utils.file_extension(file))


class NormalizarNomeProprioTestCase(TestCase):

    def test_deve_tornar_maiusculo_numero_romano(self):
        self.assertEqual("I", utils.normalizar_nome_proprio("i"))
        self.assertEqual("V", utils.normalizar_nome_proprio("v"))
        self.assertEqual("II", utils.normalizar_nome_proprio("ii"))

    def test_deve_tornar_maiusculo_uma_palavra(self):
        self.assertEqual("João", utils.normalizar_nome_proprio("joão"))

    def test_deve_tornar_maiusculo_duas_palavras(self):
        self.assertEqual("João Paulo", utils.normalizar_nome_proprio("joão paulo"))

    def test_deve_tornar_maiusculo_sigla(self):
        self.assertEqual(
            "João Pessoa PB", utils.normalizar_nome_proprio("joão pessoa pb", siglas=["PB"])
        )

    def test_nao_deve_tornar_maiusculo_preposicao(self):
        self.assertEqual("Paulo de Tarso", utils.normalizar_nome_proprio("paulo de tarso"))


class ExistsTestCase(TestCase):
    def test_deveria_ser_verdadeiro_se_valor_existe(self):
        self.assertTrue(utils.exists([True]))

    def test_deveria_ser_falso_se_valor_nao_existe(self):
        self.assertFalse(utils.exists([]))


class RetirarSimbolosCPFTestCase(TestCase):
    def test_deveria_retirar_ponto_e_traco(self):
        self.assertTrue("11111111111", utils.retirar_simbolos_cpf("111.111.111-11"))


class IsMaiorIdadeTestCase(TestCase):

    def test_deveria_lancar_excecao_se_data_vazio(self):
        with self.assertRaises(ValidationError):
            utils.is_maior_idade(None)

    @mock.patch("base.utils.idade")
    @mock.patch("base.configs.PortalConfig")
    def test_deveria_comparar_com_configuracao_definida(self, config, idade):
        config.MAIORIDADE = 18
        idade.return_value = 17
        nascimento = mock.Mock()
        self.assertFalse(utils.is_maior_idade(nascimento))

    @mock.patch("base.utils.idade")
    @mock.patch("base.configs.PortalConfig")
    def test_deveria_aceitar_datetime_no_nascimento(self, config, idade):
        config.MAIORIDADE = 18
        idade.return_value = 18
        nascimento = datetime.datetime(2020, 1, 1)
        self.assertTrue(utils.is_maior_idade(nascimento))

    @mock.patch("base.utils.idade")
    @mock.patch("base.configs.PortalConfig")
    def test_deveria_ser_verdadeiro_para_numero_maior_que_configurado(self, config, idade):
        config.MAIORIDADE = 18
        idade.return_value = 19
        nascimento = mock.Mock()
        self.assertTrue(utils.is_maior_idade(nascimento))


class IdadeTestCase(TestCase):

    def test_deveria_lancar_excecao_se_data_vazio(self):
        with self.assertRaises(ValidationError):
            utils.idade(None)

    def test_deveria_aceitar_datetime_no_nascimento(self):
        nascimento = datetime.datetime.now() - relativedelta(years=1)
        self.assertEqual(1, utils.idade(nascimento))

    def test_nascimento_no_mesmo_ano_deveria_ser_zero(self):
        nascimento = datetime.date.today()
        self.assertEqual(0, utils.idade(nascimento))

    def test_nascimento_faltando_um_dia_para_completar_ano_nao_deveveria_acrescentar(self):
        nascimento = datetime.date.today() - relativedelta(years=1) + datetime.timedelta(days=1)
        self.assertEqual(0, utils.idade(nascimento))

    def test_nascimento_no_ano_anterior_deveria_ser_um(self):
        nascimento = datetime.date.today() - relativedelta(years=1)
        self.assertEqual(1, utils.idade(nascimento))

    def test_deveria_aceitar_data_comparavel_e_data_do_nascimento(self):
        data = datetime.date.today() - relativedelta(years=1)
        nascimento = datetime.date.today() - relativedelta(years=1)
        self.assertEqual(0, utils.idade(nascimento, data))

    def test_deveria_aceitar_data_comparavel_como_datetime(self):
        data = datetime.datetime.now() - relativedelta(years=1)
        nascimento = datetime.date.today() - relativedelta(years=1)
        self.assertEqual(0, utils.idade(nascimento, data))


class TituloEleitorTestCase(TestCase):

    def test_deveria_definir_numeros_no_atributo_numero(self):
        titulo = utils.TituloEleitor("1" * 12)
        self.assertEqual("1" * 12, titulo.numero)

    def test_deveria_lancar_excecao_se_nao_houver_todos_os_numeros(self):
        with self.assertRaises(ValidationError):
            utils.TituloEleitor(["1" * 11])

    def test_deveria_lancar_excecao_se_houver_numeros_a_mais(self):
        with self.assertRaises(ValidationError):
            utils.TituloEleitor("1" * 13)

    def test_deveria_transformar_lista_de_numeros_em_string_unica(self):
        titulo = utils.TituloEleitor([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        self.assertEqual("1" * 12, titulo.numero)

    def test_deveria_remover_espacos_do_numero(self):
        titulo = utils.TituloEleitor("1111 1111 1111")
        self.assertEqual("111111111111", titulo.numero)

    def test_deveria_lancar_excecao_se_ha_caracteres_nao_esperado_no_numero(self):
        with self.assertRaises(ValidationError):
            utils.TituloEleitor([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, "a", 1])

        with self.assertRaises(ValidationError):
            utils.TituloEleitor([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, "*", 1])

        with self.assertRaises(ValidationError):
            utils.TituloEleitor([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, "^", 1])

    def test_format_number_deveria_adicionar_espacos_ao_numero(self):
        self.assertEqual("1111 1111 1111", utils.TituloEleitor.format_number("111111111111"))

    def test_format_deveria_adicionar_espacos_ao_numero(self):
        self.assertEqual("1111 1111 1111", utils.TituloEleitor("111111111111").format())

    def test_numero_deveria_ser_valido(self):
        self.assertTrue(utils.TituloEleitor("126842151295").valido())

    def test_numero_deveria_ser_invalido(self):
        self.assertFalse(utils.TituloEleitor("126842151291").valido())

    def test_validate_number_deveria_ser_valido(self):
        self.assertTrue(utils.TituloEleitor.validate_number("126842151295"))

    def test_deveria_ser_igual(self):
        self.assertTrue("1" * 12 == utils.TituloEleitor("1" * 12))

    def test_deveria_ser_diferente(self):
        self.assertTrue("2" * 12 != utils.TituloEleitor("1" * 12))

    def test_deveria_ser_diferente_para_numero_invalido(self):
        self.assertTrue("2" * 11 != utils.TituloEleitor("1" * 12))

    def test_uf_deveria_retornar_o_estado_equivalente(self):
        self.assertEqual(utils.TituloEleitor.uf_code["12"], utils.TituloEleitor("12" * 6).uf())

    def test_avaliacao_booleana_deveria_ser_valido(self):
        self.assertTrue(bool(utils.TituloEleitor("126842151295")))

    def test_str_deveria_retornar_o_numero_formatado(self):
        self.assertEqual("1268 4215 1295", str(utils.TituloEleitor("126842151295")))

    def test_repr_deveria_numero_com_nome_da_classe(self):
        self.assertEqual("TituloEleitor(126842151295)", repr(utils.TituloEleitor("126842151295")))

    def test_getitem_deveria_numero_da_posicao_correspondente(self):
        self.assertEqual("2", utils.TituloEleitor("126842151295")[1])


class SimplificarTitulacaoTestCase(TestCase):
    def test_deveria_retornar_mestrado(self):
        self.assertEqual(choices.Titulacao.MESTRADO.name, utils.simplificar_titulacao("26"))

    def test_deveria_retornar_especializacao(self):
        self.assertEqual(choices.Titulacao.ESPECIALIZACAO.name, utils.simplificar_titulacao("25"))

    def test_deveria_retornar_graduacao(self):
        self.assertEqual(choices.Titulacao.GRADUACAO.name, utils.simplificar_titulacao("23"))

    def test_deveria_retornar_doutorado(self):
        self.assertEqual(choices.Titulacao.DOUTORADO.name, utils.simplificar_titulacao("27"))

    def test_deveria_retornar_aperfeicoamento(self):
        self.assertEqual(choices.Titulacao.APERFEICOAMENTO.name, utils.simplificar_titulacao("24"))

    def test_deveria_retornar_nao_definido(self):
        self.assertEqual(choices.Titulacao.NAODEFINIDO.name, utils.simplificar_titulacao("20"))

    def test_deveria_retornar_nao_informado(self):
        self.assertEqual(choices.Titulacao.NAOINFORMADO.name, utils.simplificar_titulacao("0"))


class GetQueryString(TestCase):
    def test_data_as_query_string(self):
        self.assertEqual(
            "?key=value",
            base.custom.utils.get_query_string({"key": "value"})
        )

    def test_new_params_add_to_atual_params(self):
        self.assertEqual(
            "?key=value&new_key=new_value",
            base.custom.utils.get_query_string(
                {"key": "value"},
                new_params={"new_key": "new_value"},
            )
        )

    def test_new_params_with_none_is_not_added(self):
        self.assertEqual(
            "?key=value",
            base.custom.utils.get_query_string(
                {"key": "value", "new_key": "value"},
                new_params={"new_key": None},
            )
        )

    def test_del_params_removed_from_atual_params(self):
        self.assertEqual(
            "?",
            base.custom.utils.get_query_string(
                {"key": "value"},
                remove=["k"],
            )
        )