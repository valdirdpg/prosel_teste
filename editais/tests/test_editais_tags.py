from django.test import TestCase

from . import recipes
from .. import choices
from ..templatetags import editais_tags


class HasAnexoTestCase(TestCase):
    def test_deveria_retornar_verdadeiro_se_ha_documento_da_categoria_anexo(self):
        documento = recipes.documento.make(
            categoria=choices.CategoriaDocumentoChoices.ANEXO.name
        )
        self.assertTrue(editais_tags.has_anexo(documento.edital))

    def test_deveria_retornar_falso_se_nao_ha_documento_da_categoria_anexo(self):
        documento = recipes.documento.make(
            categoria=choices.CategoriaDocumentoChoices.EDITAL.name
        )
        self.assertFalse(editais_tags.has_anexo(documento.edital))


class DataInteresseEmEtapaTestCase(TestCase):
    def test_deveria_retornar_o_periodo_interesse_associado_a_etapa(self):
        periodo = recipes.periodo_convocacao.make(
            evento=choices.EventoCronogramaChoices.INTERESSE.name
        )
        self.assertEqual(periodo, editais_tags.data_interesse_em_etapa(periodo.etapa))

    def test_deveria_retornar_none_quando_nao_ha_periodo_interesse_na_etapa(self):
        periodo = recipes.periodo_convocacao.make(
            evento=choices.EventoCronogramaChoices.ANALISE.name
        )
        self.assertIsNone(editais_tags.data_interesse_em_etapa(periodo.etapa))
