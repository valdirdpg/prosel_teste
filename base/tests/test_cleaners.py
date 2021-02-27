from django.test import TestCase

from .. import cleaners


class RemoveSimbolosCPFTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.cpf = cleaners.remove_simbolos_cpf("111.111.111-11")

    def test_deveria_remover_pontos(self):
        self.assertNotIn(".", self.cpf)

    def test_deveria_remover_traco(self):
        self.assertNotIn("-", self.cpf)

    def test_deveria_remover_pontos_e_traco(self):
        self.assertEqual("11111111111", self.cpf)

    def test_deveria_manter_a_mesma_quantidade_de_numeros(self):
        self.assertEqual(11, len(self.cpf))
