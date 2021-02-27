from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from .. import validators


class CPFValidatorTestCase(TestCase):

    @mock.patch("base.validators.CPF")
    def test_numero_valido_nao_deveria_lancar_excecao(self, cpf):
        cpf.return_value.valido.return_value = True
        numero_valido = mock.Mock()
        self.assertIsNone(validators.cpf_validator(numero_valido))

    @mock.patch("base.validators.CPF")
    def test_numero_invalido_deveria_lancar_validation_error_exception_ao_instanciar(self, cpf):
        cpf.side_effect = ValidationError("Mensagem")
        numero_invalido = mock.Mock()
        with self.assertRaises(ValidationError):
            validators.cpf_validator(numero_invalido)

    @mock.patch("base.validators.CPF")
    def test_numero_invalido_deveria_lancar_validation_error_exception_no_is_valido(self, cpf):
        cpf.return_value.valido.return_value = False
        numero_invalido = mock.Mock()
        with self.assertRaises(ValidationError):
            validators.cpf_validator(numero_invalido)


class TituloEleitorValidatorTestCase(TestCase):

    @mock.patch("base.validators.TituloEleitor")
    def test_numero_valido_nao_deveria_lancar_excecao(self, titulo):
        titulo.return_value.valido.return_value = True
        numero_valido = mock.Mock()
        self.assertIsNone(validators.titulo_eleitor_validator(numero_valido))

    @mock.patch("base.validators.TituloEleitor")
    def test_numero_invalido_deveria_lancar_validation_error_exception_ao_instanciar(self, titulo):
        titulo.side_effect = ValidationError("Mensagem")
        numero_invalido = mock.Mock()
        with self.assertRaises(ValidationError):
            validators.titulo_eleitor_validator(numero_invalido)

    @mock.patch("base.validators.TituloEleitor")
    def test_numero_invalido_deveria_lancar_validation_error_exception_no_is_valido(self, titulo):
        titulo.return_value.valido.return_value = False
        numero_invalido = mock.Mock()
        with self.assertRaises(ValidationError):
            validators.titulo_eleitor_validator(numero_invalido)


class TelefoneValidatorTestCase(TestCase):

    def test_numero_valido_nao_deveria_lancar_excecao(self):
        numeros_validos = [
            "(99)999-9999",
            "(99)9999-9999",
            "(99)99999-9999",
            "(99) 999-9999",
            "(99) 9999-9999",
            "(99) 99999-9999",
        ]
        for numero in numeros_validos:
            self.assertIsNone(validators.telefone_validator(numero))

    def test_numero_invalido_deveria_lancar_excecao(self):
        numeros_invalidos = [
            "(99)9999999",
            "99)9999-9999",
            "(9999999-9999",
            " 999-9999",
            "9999-9999",
            "99999999999",
            "",
        ]
        for numero in numeros_invalidos:
            with self.assertRaises(ValidationError):
                validators.telefone_validator(numero)


class CEPValidatorTestCase(TestCase):

    def test_numero_valido_nao_deveria_lancar_excecao(self):
        self.assertIsNone(validators.cep_validator("99.999-999"))

    def test_numero_invalido_deveria_lancar_excecao(self):
        numeros_invalidos = [
            "99999999",
            "99.999999",
            "99.999.999",
            "99-999-999",
            "99999-999",
            "",
        ]
        for numero in numeros_invalidos:
            with self.assertRaises(ValidationError):
                validators.cep_validator(numero)


class NomeDePessoaValidatorTestCase(TestCase):

    def test_deveria_ser_valido_se_tiver_nome_e_sobrenome(self):
        self.assertIsNone(validators.nome_de_pessoa_validator("João Silva"))

    def test_deveria_ser_valido_se_tiver_espacos_em_branco_entre_as_palavras(self):
        self.assertIsNone(validators.nome_de_pessoa_validator("João Silva"))

    def test_deveria_ser_valido_se_tiver_apenas_letras(self):
        self.assertIsNone(validators.nome_de_pessoa_validator("João Silva"))

    def test_deveria_ser_invalido_se_tiver_apenas_uma_palavra(self):
        with self.assertRaises(ValidationError):
            validators.nome_de_pessoa_validator("João")

    def test_deveria_ser_invalido_se_a_palavra_for_grande_demais(self):
        with self.assertRaises(ValidationError):
            validators.nome_de_pessoa_validator(f"{'a' * 31} {'b' * 31}")

    def test_deveria_ser_invalido_se_tiver_pontuacao(self):
        with self.assertRaises(ValidationError):
            validators.nome_de_pessoa_validator("João Silva!")

    def test_deveria_ser_invalido_se_tiver_numeros(self):
        with self.assertRaises(ValidationError):
            validators.nome_de_pessoa_validator("João Silva 2")

    def test_deveria_ser_invalido_se_tiver_caracteres_especiais(self):
        with self.assertRaises(ValidationError):
            validators.nome_de_pessoa_validator("João Silva*")
