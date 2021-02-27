from django.test import TestCase

from ..models.inscricao import Modalidade
from processoseletivo.models import ModalidadeEnum
from model_mommy import mommy


class ModalidadeQuerySetTestCase(TestCase):
    fixtures = ['modalidade.json']

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        mommy.make(Modalidade, equivalente_id=ModalidadeEnum.escola_publica_pcd)
        mommy.make(Modalidade, equivalente_id=ModalidadeEnum.escola_publica)
        mommy.make(Modalidade, equivalente_id=ModalidadeEnum.rurais)
        mommy.make(Modalidade, equivalente_id=ModalidadeEnum.deficientes)
        mommy.make(Modalidade, equivalente_id=ModalidadeEnum.ampla_concorrencia)
        cls.modalidades = Modalidade.objects.ordenação_por_tipo_escola()

    def test_deveria_retornar_ampla_na_primeira_posicao(self):
        ampla = Modalidade.objects.get(equivalente_id=ModalidadeEnum.ampla_concorrencia)
        self.assertEqual(ampla, self.modalidades[0])

    def test_deveria_retornar_deficientes_na_segunda_posicao(self):
        deficientes = Modalidade.objects.get(equivalente_id=ModalidadeEnum.deficientes)
        self.assertEqual(deficientes, self.modalidades[1])

    def test_deveria_retornar_rurais_na_terceira_posicao(self):
        rurais = Modalidade.objects.get(equivalente_id=ModalidadeEnum.rurais)
        self.assertEqual(rurais, self.modalidades[2])

    def test_deveria_retornar_escola_publica_pcd_na_quarta_posicao(self):
        escola_publica_pcd = Modalidade.objects.get(equivalente_id=ModalidadeEnum.escola_publica_pcd)
        self.assertEqual(escola_publica_pcd, self.modalidades[3])

    def test_deveria_retornar_escola_publica_na_quinta_posicao(self):
        escola_publica = Modalidade.objects.get(equivalente_id=ModalidadeEnum.escola_publica)
        self.assertEqual(escola_publica, self.modalidades[4])
