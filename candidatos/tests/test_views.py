from unittest import mock

from django.test import TestCase
from django.urls import reverse
from model_mommy import mommy

import base.tests.recipes
import cursos.models
import processoseletivo.tests.recipes
import psct.permissions
from base.tests.mixins import UserTestMixin
from .. import permissions
from .. import views


class ConvocacoesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.etapa = processoseletivo.tests.recipes.etapa.make(publica=True)
        with mock.patch.multiple(
                cursos.models.Campus,
                cria_usuarios_diretores=mock.DEFAULT,
                adiciona_permissao_diretores=mock.DEFAULT,
                remove_permissao_diretores=mock.DEFAULT,
        ):
            cls.chamada = processoseletivo.tests.recipes.chamada.make(etapa=cls.etapa)
            cls.inscricao = processoseletivo.tests.recipes.inscricao.make(
                chamada=cls.chamada,
            )
        mommy.make("editais.PeriodoConvocacao", etapa=cls.etapa, evento="INTERESSE")
        cls.user = base.tests.recipes.user.make()
        cls.user.set_password("123")
        cls.user.save()
        cls.inscricao.candidato.pessoa.user = cls.user
        cls.inscricao.candidato.pessoa.save()

    def test_candidato_pode_ver_suas_convocacoes(self):
        self.client.login(username=self.user.username, password="123")
        response = self.client.get(reverse("candidato_convocacoes"))
        self.assertContains(response, f"Convocações de {self.inscricao.candidato.pessoa}")
        self.assertContains(response, self.inscricao.curso.nome)


class DadosBasicosUpdateViewTestCase(TestCase):
    def test_group_required_deveria_estar_configurado_corretamente(self):
        self.assertEqual(
            permissions.Candidatos.name,
            views.DadosBasicosUpdateView.group_required
        )


class DadosBasicosUpdateViewFuncionalTestCase(UserTestMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.Candidatos().sync()
        base.tests.recipes.pessoa_fisica.make(user=cls.usuario_base)
        permissions.Candidatos.add_user(cls.usuario_base)

    def setUp(self) -> None:
        super().setUp()
        self.client.login(**self.usuario_base.credentials)
        self.response = self.client.get(reverse("dados_basicos_candidato"))

    def test_candidato_deveria_acessar_pagina_de_alteracao_dados(self):
        self.assertEqual(200, self.response.status_code)


class DadosBasicosUpdateViewCandidatoPSCTFuncionalTestCase(UserTestMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.Candidatos().sync()
        base.tests.recipes.pessoa_fisica.make(
            user=cls.usuario_base
        )
        psct.permissions.CandidatosPSCT.add_user(cls.usuario_base)

    def setUp(self) -> None:
        super().setUp()
        self.client.login(**self.usuario_base.credentials)
        self.response = self.client.get(reverse("dados_basicos_candidato"))

    def test_candidato_psct_nao_deveria_acessar_pagina_de_alteracao_dados(self):
        self.assertEqual(403, self.response.status_code)
