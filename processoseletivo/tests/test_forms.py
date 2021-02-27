from datetime import date
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils.formats import date_format
from model_mommy import mommy

import base.models
import base.tests.recipes
from base.tests.mixins import UserTestMixin
from cursos.tests import mixins
from . import recipes
from .. import forms
from .. import models
from .. import permissions


class PeriodoConvocacaoFormTestCase(TestCase):
    def test_campos_deveriam_ser_obrigatorios(self):
        form = forms.PeriodoConvocacaoInlineForm(data={})
        form.is_valid()
        self.assertIn("Este campo é obrigatório.", form.errors["nome"])
        self.assertIn("Este campo é obrigatório.", form.errors["inicio"])
        self.assertIn("Este campo é obrigatório.", form.errors["fim"])
        self.assertIn("Este campo é obrigatório.", form.errors["evento"])


class ServidorLotacaoTestCase(mixins.DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.campus = mommy.make("cursos.Campus")
        cls.user = base.tests.recipes.user.make(username="1234567")
        cls.servidor = mommy.make("cursos.Servidor", matricula="1234567")
        cls.request = Mock()
        cls.request.user = cls.user
        permissions.AdministradoresSistemicosdeChamadas().sync()
        permissions.AdministradoresSistemicosdeChamadas.add_user(cls.user)

    @patch("ajax_select.fields.AutoCompleteSelectField.clean")
    @patch("processoseletivo.forms.validate_user")
    def test_formulario_deveria_ser_valido(self, validate_user, get_servidor):
        validate_user.return_value = None
        get_servidor.return_value = self.servidor
        data = {"campi": [self.campus.id], "servidor": self.servidor.id}
        form = forms.ServidorLotacaoForm(data=data, request=self.request)
        self.assertTrue(form.is_valid())

    @patch("ajax_select.fields.AutoCompleteSelectField.clean")
    @patch("processoseletivo.forms.validate_user")
    def test_deveria_adicionar_lotacao_para_servidor(self, validate_user, get_servidor):
        validate_user.return_value = None
        get_servidor.return_value = self.servidor
        data = {"campi": [self.campus.id], "servidor": self.servidor.id}
        form = forms.ServidorLotacaoForm(data=data, request=self.request)
        form.is_valid()
        form.save()
        user_atualizado = models.User.objects.get(id=self.user.id)
        self.assertIn(self.campus, user_atualizado.lotacoes.all())


class AnaliseDocumentalFormTestCase(mixins.DiretorEnsinoPermissionData, UserTestMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.data = {
            'confirmacao_interesse': recipes.confirmacao.make().id,
            'situacao_final': True,
            'observacao': 'Alguma'
        }

    def test_campos_obrigatorios(self):
        form = forms.AnaliseDocumentalForm(data={})
        form.is_valid()
        self.assertIn('Este campo é obrigatório.', form.errors["observacao"])
        self.assertIn('Este campo é obrigatório.', form.errors["situacao_final"])
        self.assertIn('Este campo é obrigatório.', form.errors["confirmacao_interesse"])

    def test_formulario_deveria_ser_valido(self):
        form = forms.AnaliseDocumentalForm(data=self.data)
        self.assertTrue(form.is_valid())

    def test_deveriar_criar_analise_documental(self):
        form = forms.AnaliseDocumentalForm(data=self.data)
        form.user = self.usuario_base
        form.is_valid()
        analise = form.save()
        self.assertTrue(models.AnaliseDocumental.objects.filter(id=analise.id).exists())


class TipoAnaliseFormTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.data = {
            'nome': models.TipoAnalise.TIPO_AVALIACAO_EEP,
            'setor_responsavel': 'Setor',
            'descricao': "Alguma descrição",
            'modalidade': [mommy.make(models.Modalidade).id],
            'situacao': True
        }

    def test_campos_obrigatorios(self):
        form = forms.TipoAnaliseForm(data={})
        form.is_valid()
        self.assertIn('Este campo é obrigatório.', form.errors["nome"])
        self.assertIn('Este campo é obrigatório.', form.errors["setor_responsavel"])
        self.assertIn('Este campo é obrigatório.', form.errors["descricao"])
        self.assertIn('Este campo é obrigatório.', form.errors["modalidade"])
        self.assertIn('Este campo é obrigatório.', form.errors["situacao"])

    def test_formulario_deveria_ser_valido(self):
        form = forms.TipoAnaliseForm(data=self.data)
        self.assertTrue(form.is_valid())

    def test_deveriar_criar_tipo_analise(self):
        form = forms.TipoAnaliseForm(data=self.data)
        form.is_valid()
        tipo = form.save()
        self.assertTrue(models.TipoAnalise.objects.filter(id=tipo.id).exists())


class ConfirmacaoInteresseFormTestCase(mixins.DiretorEnsinoPermissionData, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.etapa = recipes.etapa.make(encerrada=False)
        cls.inscricao = recipes.inscricao.make()
        cls.data = {
            'inscricao': cls.inscricao.id,
            'etapa': cls.etapa.id
        }

    def test_campos_obrigatorios(self):
        form = forms.ConfirmacaoInteresseForm(data={})
        form.is_valid()
        self.assertIn('Este campo é obrigatório.', form.errors["inscricao"])
        self.assertIn('Este campo é obrigatório.', form.errors["etapa"])

    def test_formulario_deveria_ser_valido(self):
        form = forms.ConfirmacaoInteresseForm(data=self.data)
        self.assertTrue(form.is_valid())

    def test_deveriar_criar_confirmacao(self):
        form = forms.ConfirmacaoInteresseForm(data=self.data)
        form.is_valid()
        confirmacao = form.save()
        self.assertTrue(models.ConfirmacaoInteresse.objects.filter(id=confirmacao.id).exists())


class AvaliacaoDocumentalFormTestCase(mixins.DiretorEnsinoPermissionData, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.analise = recipes.analise.make()
        cls.tipo_analise = recipes.tipo_analise.make()
        cls.data = {
            'situacao': True,
            'observacao': 'Alguma',
            'analise_documental': cls.analise.id,
            'data': date_format(date.today(), format="SHORT_DATE_FORMAT"),
            'servidor_setor': 'Servidor',
            'tipo_analise': cls.tipo_analise.id
        }

    def test_campos_obrigatorios(self):
        form = forms.AvaliacaoDocumentalForm(data={})
        form.is_valid()
        self.assertIn('Este campo é obrigatório.', form.errors["situacao"])
        self.assertIn('Este campo é obrigatório.', form.errors["analise_documental"])
        self.assertIn('Este campo é obrigatório.', form.errors["data"])
        self.assertIn('Este campo é obrigatório.', form.errors["servidor_setor"])
        self.assertIn('Este campo é obrigatório.', form.errors["tipo_analise"])
        self.assertNotIn('observacao', form.errors)

    @patch('processoseletivo.models.AvaliacaoDocumental.pode_editar')
    def test_formulario_deveria_ser_valido(self, pode_editar):
        pode_editar.return_value = True
        form = forms.AvaliacaoDocumentalForm(data=self.data)
        self.assertTrue(form.is_valid())

    @patch('processoseletivo.models.AvaliacaoDocumental.pode_editar')
    def test_deveriar_criar_confirmacao(self, pode_editar):
        pode_editar.return_value = True
        form = forms.AvaliacaoDocumentalForm(data=self.data)
        form.is_valid()
        avaliacao = form.save()
        self.assertTrue(models.AvaliacaoDocumental.objects.filter(id=avaliacao.id).exists())


class RecursoFormTestCase(mixins.DiretorEnsinoPermissionData, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.inscricao = recipes.inscricao.make()
        cls.data = {
            'analise_documental': recipes.analise.make().id,
            'protocolo': 'Protocolo 1',
            'justificativa': 'Justificativa 1',
            'status_recurso': "INDEFERIDO",
        }

    def test_campos_obrigatorios(self):
        form = forms.RecursoForm(data={})
        form.is_valid()
        self.assertIn('Este campo é obrigatório.', form.errors["analise_documental"])
        self.assertIn('Este campo é obrigatório.', form.errors["protocolo"])
        self.assertIn('Este campo é obrigatório.', form.errors["justificativa"])
        self.assertIn('Este campo é obrigatório.', form.errors["status_recurso"])

    def test_formulario_deveria_ser_valido(self):
        form = forms.RecursoForm(data=self.data)
        self.assertTrue(form.is_valid())

    def test_deveriar_criar_recurso(self):
        form = forms.RecursoForm(data=self.data)
        form.is_valid()
        recurso = form.save()
        self.assertTrue(models.Recurso.objects.filter(id=recurso.id).exists())


class VagaFormTestCase(mixins.DiretorEnsinoPermissionData, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.data = {
            'edicao': recipes.edicao.make().id,
            'curso': mommy.make('cursos.CursoSelecao').id,
            'modalidade': recipes.modalidade.make().id,
            'modalidade_primaria': recipes.modalidade.make().id,
            'candidato': recipes.candidato.make().id
        }

    def test_campos_obrigatorios(self):
        form = forms.VagaForm(data={})
        form.is_valid()
        self.assertIn('Este campo é obrigatório.', form.errors["edicao"])
        self.assertIn('Este campo é obrigatório.', form.errors["curso"])
        self.assertIn('Este campo é obrigatório.', form.errors["modalidade"])
        self.assertIn('Este campo é obrigatório.', form.errors["modalidade_primaria"])
        self.assertIn('Este campo é obrigatório.', form.errors["candidato"])

    def test_formulario_deveria_ser_valido(self):
        form = forms.VagaForm(data=self.data)
        form.is_valid()
        self.assertTrue(form.is_valid())

    def test_deveriar_criar_recurso(self):
        form = forms.VagaForm(data=self.data)
        form.is_valid()
        vaga = form.save()
        self.assertTrue(models.Vaga.objects.filter(id=vaga.id).exists())
