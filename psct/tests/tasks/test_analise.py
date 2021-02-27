from unittest import expectedFailure, mock

from django.test import TestCase
from django.urls import reverse

from cursos.permissions import DiretoresdeEnsino
from .. import recipes
from ... import permissions
from ...models import FaseAnalise, ProgressoAnalise
from ...tasks.analise import importar


class ImportarTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        DiretoresdeEnsino().sync()
        permissions.AvaliadorPSCT().sync()
        cls.fase = recipes.fase_analise.make()

    @expectedFailure
    def test_deve_lancar_excecao_de_objeto_nao_existente(self):
        with self.assertRaises(FaseAnalise.DoesNotExist):
            importar(mock.Mock())

    @mock.patch("psct.models.analise.ProgressoAnalise.objects.bulk_create")
    @mock.patch("psct.models.analise.InscricaoPreAnalise.create_many")
    def test_deve_chamar_create_many_de_inscricoes_pre_analise_da_fase(
            self, create_many, bulk_create
    ):
        importar(self.fase.pk)
        create_many.assert_called_once()

    @mock.patch("psct.models.analise.ProgressoAnalise.objects.bulk_create")
    @mock.patch("psct.models.analise.InscricaoPreAnalise.create_many")
    def test_deve_chamar_bulk_create_de_progresso_analise_da_modalidade_por_fase(
            self, create_many, bulk_create
    ):
        importar(self.fase.pk)
        bulk_create.assert_called_once()

    @mock.patch("psct.models.analise.ProgressoAnalise.objects.bulk_create")
    @mock.patch("psct.models.analise.InscricaoPreAnalise.create_many")
    def test_deve_chamar_bulk_create_com_objetos_corretos(self, create_many, bulk_create):
        vaga_edital = recipes.modalidade_vaga_curso_edital.make(
            curso_edital__edital=self.fase.edital,
        )
        importar(self.fase.pk)
        obj_exemplo = ProgressoAnalise(
            fase=self.fase,
            curso=vaga_edital.curso_edital.curso,
            modalidade=vaga_edital.modalidade,
            meta=(vaga_edital.quantidade_vagas * vaga_edital.multiplicador)
        )
        (args, ) = bulk_create.call_args[0]
        self.assertIsInstance(args, list)
        self.assertEqual(obj_exemplo.fase, args[0].fase)
        self.assertEqual(obj_exemplo.curso, args[0].curso)
        self.assertEqual(obj_exemplo.modalidade, args[0].modalidade)
        self.assertEqual(obj_exemplo.meta, args[0].meta)

    @mock.patch("psct.models.analise.ProgressoAnalise.objects.bulk_create")
    @mock.patch("psct.models.analise.InscricaoPreAnalise.create_many")
    def test_deve_retornar_mensagem_de_confirmacao_da_execucao(self, create_many, bulk_create):
        result = importar(self.fase.pk)
        self.assertDictEqual(
            {"url": reverse("list_inscricao_psct"), "message": "Importação realizada com sucesso!"},
            result
        )
