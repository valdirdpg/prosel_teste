import datetime
from unittest import mock

from django.core.exceptions import ValidationError
from django.core.files import File
from django.test import TestCase
from django.urls import reverse
from faker import Faker

from . import recipes
from .. import choices

faker = Faker("pt_BR")


class EditalTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.edital = recipes.edital.make()

    def test_str_deveria_conter_nome_numero_e_ano(self):
        self.assertEqual(
            str(self.edital),
            f"{self.edital.nome} - {self.edital.numero}/{self.edital.ano}",
        )

    def test_has_anexo_deveria_ser_verdadeiro_se_ha_documento_do_tipo_anexo(self):
        documento = recipes.documento.make(
            categoria=choices.CategoriaDocumentoChoices.ANEXO.name
        )
        self.assertTrue(documento.edital.has_anexo())

    def test_has_anexo_deveria_ser_falso_se_ha_qualquer_outro_tipo_documento(self):
        categoria_qualquer = choices.CategoriaDocumentoChoices.RECURSO.name
        documento = recipes.documento.make(categoria=categoria_qualquer)
        self.assertFalse(documento.edital.has_anexo())

    def test_has_anexo_deveria_ser_falso_se_nao_ha_documento(self):
        self.assertFalse(self.edital.has_anexo())

    def test_has_local_prova_deveria_ser_verdadeiro_se_ha_documento_do_tipo_local_prova(
        self
    ):
        documento = recipes.documento.make(
            categoria=choices.CategoriaDocumentoChoices.LOCALPROVA.name
        )
        self.assertTrue(documento.edital.has_local_prova())

    def test_has_local_prova_deveria_ser_falso_se_ha_qualquer_outro_tipo_documento(
        self
    ):
        categoria_qualquer = choices.CategoriaDocumentoChoices.RECURSO.name
        documento = recipes.documento.make(categoria=categoria_qualquer)
        self.assertFalse(documento.edital.has_local_prova())

    def test_has_local_prova_deveria_ser_falso_se_nao_ha_documento(self):
        self.assertFalse(self.edital.has_local_prova())

    def test_has_recurso_deveria_ser_verdadeiro_se_ha_documento_do_tipo_recurso(self):
        documento = recipes.documento.make(
            categoria=choices.CategoriaDocumentoChoices.RECURSO.name
        )
        self.assertTrue(documento.edital.has_recurso())

    def test_has_recurso_deveria_ser_falso_se_ha_qualquer_outro_tipo_documento(self):
        categoria_qualquer = choices.CategoriaDocumentoChoices.LOCALPROVA.name
        documento = recipes.documento.make(categoria=categoria_qualquer)
        self.assertFalse(documento.edital.has_recurso())

    def test_has_recurso_deveria_ser_falso_se_nao_ha_documento(self):
        self.assertFalse(self.edital.has_recurso())

    def test_has_resultado_deveria_ser_verdadeiro_se_ha_documento_do_tipo_resultado(
        self
    ):
        documento = recipes.documento.make(
            categoria=choices.CategoriaDocumentoChoices.RESULTADO.name
        )
        self.assertTrue(documento.edital.has_resultado())

    def test_has_resultado_deveria_ser_falso_se_ha_qualquer_outro_tipo_documento(self):
        categoria_qualquer = choices.CategoriaDocumentoChoices.LOCALPROVA.name
        documento = recipes.documento.make(categoria=categoria_qualquer)
        self.assertFalse(documento.edital.has_resultado())

    def test_has_resultado_deveria_ser_falso_se_nao_ha_documento(self):
        self.assertFalse(self.edital.has_resultado())

    def test_has_prova_gabarito_deveria_ser_verdadeiro_se_ha_documento_de_gabarito(
        self
    ):
        documento = recipes.documento.make(
            categoria=choices.CategoriaDocumentoChoices.GABARITO.name
        )
        self.assertTrue(documento.edital.has_prova_gabarito())

    def test_has_prova_gabarito_deveria_ser_verdadeiro_se_ha_documento_de_prova(self):
        documento = recipes.documento.make(
            categoria=choices.CategoriaDocumentoChoices.PROVA.name
        )
        self.assertTrue(documento.edital.has_prova_gabarito())

    def test_has_prova_gabarito_deveria_ser_falso_se_nao_ha_documento(self):
        self.assertFalse(self.edital.has_prova_gabarito())

    @mock.patch("editais.models.Cronograma.is_vigente")
    def test_inscricoes_abertas_deveria_ser_verdadeiro_se_ha_cronograma_inscricao_vigente(
        self, is_vigente
    ):
        is_vigente.return_value = True
        periodo = recipes.periodo_selecao.make(inscricao=True)
        self.assertTrue(periodo.edital.inscricoes_abertas())

    @mock.patch("editais.models.Cronograma.is_vigente")
    def test_inscricoes_abertas_deveria_ser_falso_se_ha_cronograma_inscricao_encerrado(
        self, is_vigente
    ):
        is_vigente.return_value = False
        periodo = recipes.periodo_selecao.make(inscricao=True)
        self.assertFalse(periodo.edital.inscricoes_abertas())

    def test_inscricoes_abertas_deveria_ser_falso_se_nao_ha_cronograma(self):
        self.assertFalse(self.edital.inscricoes_abertas())

    @mock.patch("editais.models.Cronograma.is_vigente")
    def test_inscricoes_abertas_deveria_ser_falso_se_ha_cronograma_inscricao_a_iniciar(
        self, is_vigente
    ):
        is_vigente.return_value = False
        periodo = recipes.periodo_selecao.make(inscricao=True)
        self.assertFalse(periodo.edital.inscricoes_abertas())

    def test_iniciou_inscricoes_deveria_ser_verdadeiro_se_ha_cronograma_inscricao_vigente(
        self
    ):
        periodo = recipes.periodo_selecao.make(inscricao=True)
        self.assertTrue(periodo.edital.iniciou_inscricoes())

    def test_iniciou_inscricoes_deveria_ser_falso_se_inicio_esta_no_futuro(self):
        periodo = recipes.periodo_selecao.make(
            inscricao=True, inicio=datetime.date.today() + datetime.timedelta(days=1)
        )
        self.assertFalse(periodo.edital.iniciou_inscricoes())

    def test_iniciou_inscricoes_deveria_ser_falso_se_nao_ha_cronograma(self):
        self.assertFalse(self.edital.iniciou_inscricoes())

    def test_get_absolute_url_deveria_estar_corretamente_formatado(self):
        expected_url = reverse(
            "edicao",
            args=[self.edital.edicao.processo_seletivo.id, self.edital.edicao.id],
        )
        self.assertEqual(expected_url, self.edital.get_absolute_url())


class DocumentoTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.documento = recipes.documento.make()

    def test_str_deveria_retornar_nome(self):
        self.assertEqual(str(self.documento), self.documento.nome)

    def test_clean_deveria_validar_se_arquivo_e_link_forem_preenchidos_ao_mesmo_tempo(
        self
    ):
        documento = recipes.documento.make(
            link_arquivo_externo=faker.url(), arquivo=faker.file_path()
        )
        with self.assertRaises(ValidationError) as exception:
            documento.clean()
        exception = exception.exception
        self.assertIn(
            "Você deve escolher entre definir um arquivo ou um link de arquivo externo.",
            exception.messages,
        )

    def test_clean_deveria_validar_se_arquivo_e_link_nao_forem_preenchidos(self):
        with self.assertRaises(ValidationError) as exception:
            self.documento.clean()
        exception = exception.exception
        self.assertIn(
            "Você deve escolher entre definir um arquivo ou um link de arquivo externo.",
            exception.messages,
        )

    def test_clean_deveria_ser_valido_se_arquivo_for_preenchido(self):
        documento = recipes.documento.make(arquivo=faker.file_path())
        self.assertIsNone(documento.clean())

    def test_clean_deveria_ser_valido_se_link_arquivo_externo_for_preenchido(self):
        documento = recipes.documento.make(link_arquivo_externo=faker.url())
        self.assertIsNone(documento.clean())

    def test_campo_arquivo_deveria_aceitar_pdf(self):
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = "test.pdf"
        documento = recipes.documento.make(arquivo=file_mock)
        self.assertIsNotNone(
            documento.arquivo.field.clean(documento.arquivo.file, documento)
        )

    def test_campo_arquivo_deveria_rejeitar_arquivos_diferente_de_pdf(self):
        not_allowed = {"txt", "doc", "dot", "docx", "odt", "xls", "xlsx"}
        for extension in not_allowed:
            file_mock = mock.MagicMock(spec=File)
            file_mock.name = f"test.{extension}"
            documento = recipes.documento.make(arquivo=file_mock)
            with self.assertRaises(ValidationError):
                documento.arquivo.field.clean(documento.arquivo.file, documento)


class NivelSelecaoTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.nivel_selecao = recipes.nivel_selecao.make()

    def test_str_deveria_conter_nome(self):
        self.assertEqual(str(self.nivel_selecao), self.nivel_selecao.nome)


class CronogramaTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.cronograma = recipes.cronograma.make()

    def test_str_deveria_conter_nome_e_periodo(self):
        expected = (
            f"{self.cronograma.nome} - {self.cronograma.inicio} à {self.cronograma.fim}"
        )
        self.assertEqual(expected, str(self.cronograma))

    def test_is_encerrado_deveria_retornar_verdadeiro_quando_fim_foi_ontem(self):
        cronograma = recipes.cronograma.make(
            fim=datetime.date.today() - datetime.timedelta(days=1)
        )
        self.assertTrue(cronograma.is_encerrado())

    def test_is_encerrado_deveria_retornar_falso_quando_fim_eh_hoje(self):
        cronograma = recipes.cronograma.make(fim=datetime.date.today())
        self.assertFalse(cronograma.is_encerrado())

    def test_is_encerrado_deveria_retornar_falso_quando_fim_eh_amanha(self):
        cronograma = recipes.cronograma.make(
            fim=datetime.date.today() + datetime.timedelta(days=1)
        )
        self.assertFalse(cronograma.is_encerrado())

    def test_is_vigente_deveria_retornar_falso_quando_iniciara_amanha(self):
        cronograma = recipes.cronograma.make(
            inicio=datetime.date.today() + datetime.timedelta(days=1),
            fim=datetime.date.today() + datetime.timedelta(days=1),
        )
        self.assertFalse(cronograma.is_vigente())

    def test_is_vigente_deveria_retornar_verdadeiro_quando_iniciou_hoje(self):
        cronograma = recipes.cronograma.make(inicio=datetime.date.today())
        self.assertTrue(cronograma.is_vigente())

    def test_is_vigente_deveria_retornar_verdadeiro_dias_apos_o_inicio(self):
        cronograma = recipes.cronograma.make(
            inicio=datetime.date.today() - datetime.timedelta(days=1),
            fim=datetime.date.today(),
        )
        self.assertTrue(cronograma.is_vigente())

    def test_is_vigente_deveria_retornar_verdadeiro_no_dia_do_encerramento(self):
        cronograma = recipes.cronograma.make(fim=datetime.date.today())
        self.assertTrue(cronograma.is_vigente())

    def test_is_vigente_deveria_retornar_verdadeiro_dias_antes_do_encerramento(self):
        cronograma = recipes.cronograma.make(
            inicio=datetime.date.today(),
            fim=datetime.date.today() + datetime.timedelta(days=1),
        )
        self.assertTrue(cronograma.is_vigente())

    def test_is_vigente_deveria_retornar_falso_quando_encerrado_ontem(self):
        cronograma = recipes.cronograma.make(
            inicio=datetime.date.today() - datetime.timedelta(days=1),
            fim=datetime.date.today() - datetime.timedelta(days=1),
        )
        self.assertFalse(cronograma.is_vigente())


class PeriodoConvocacaoTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.periodo = recipes.periodo_convocacao.make()

    def test_is_manifestacao_interesse_deveria_retornar_verdadeiro_para_evento_interesse(
        self
    ):
        periodo = recipes.periodo_convocacao.make(
            evento=choices.EventoCronogramaChoices.INTERESSE.name
        )
        self.assertTrue(periodo.is_manifestacao_interesse())

    def test_is_manifestacao_interesse_deveria_retornar_falso_para_outro_evento(self):
        periodo = recipes.periodo_convocacao.make(
            evento=choices.EventoCronogramaChoices.ANALISE.name
        )
        self.assertFalse(periodo.is_manifestacao_interesse())
