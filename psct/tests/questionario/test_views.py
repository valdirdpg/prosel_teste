import datetime
from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

import base.models
import processoseletivo.tests.recipes
from base.tests.mixins import UserTestMixin
from .. import recipes


class QuestionarioCreateFunctionalTestCase(UserTestMixin, TestCase):

    def test_candidato_nao_psct_nao_deveria_acessar_questionario(self):
        processoseletivo.tests.recipes.candidato.make(
            pessoa__user=self.usuario_base
        )
        modelo_questionario = recipes.modelo_questionario.make()
        recipes.processo_inscricao.make(
            edital=modelo_questionario.edital,
        )
        self.client.login(**self.usuario_base.credentials)
        response = self.client.get(
            reverse("responder_questionario_psct", args=[modelo_questionario.edital_id])
        )
        self.assertEqual(403, response.status_code)

    def test_candidato_nao_deveria_acessar_fora_do_periodo_inscricao(self):
        recipes.candidato.make(
            user=self.usuario_base
        )
        processo_inscricao = recipes.processo_inscricao.make(
            data_inicio=datetime.date.today() - datetime.timedelta(days=1),
            data_encerramento=datetime.date.today() - datetime.timedelta(days=1),

        )
        self.client.login(**self.usuario_base.credentials)
        response = self.client.get(
            reverse("responder_questionario_psct", args=[processo_inscricao.edital_id])
        )
        self.assertEqual(403, response.status_code)

    def test_candidato_nao_deveria_acessar_se_edital_nao_tem_modelo_questionario(self):
        recipes.candidato.make(
            user=self.usuario_base
        )
        processo_inscricao = recipes.processo_inscricao.make()
        self.client.login(**self.usuario_base.credentials)
        response = self.client.get(
            reverse("responder_questionario_psct", args=[processo_inscricao.edital_id])
        )
        self.assertEqual(404, response.status_code)

    @mock.patch.object(base.models.PessoaFisica, "is_atualizado_recentemente")
    def test_usuario_nao_atualizou_recentemente_deveria_ser_redirecionado_para_dados_basicos(
            self, is_atualizado_recentemente
    ):
        is_atualizado_recentemente.return_value = False
        recipes.candidato.make(
            user=self.usuario_base
        )
        modelo_questionario = recipes.modelo_questionario.make()
        recipes.processo_inscricao.make(
            edital=modelo_questionario.edital,
        )
        self.client.login(**self.usuario_base.credentials)
        response = self.client.get(
            reverse("responder_questionario_psct", args=[modelo_questionario.edital_id])
        )
        url = (
            f'{reverse("dados_basicos_psct")}?next='
            f'{reverse("responder_questionario_psct", args=[modelo_questionario.edital_id])}'
        )
        self.assertRedirects(response, url, fetch_redirect_response=False)

    def test_usuario_nao_autenticado_deveria_ser_redirecional_para_o_login(self):
        modelo_questionario = recipes.modelo_questionario.make()
        self.client.logout()
        url = reverse("responder_questionario_psct", args=[modelo_questionario.edital_id])
        response = self.client.get(url)
        self.assertRedirects(
            response, f"{settings.LOGIN_URL}?next={url}", fetch_redirect_response=False
        )

    def test_usuario_deveria_conseguir_acessar_em_periodo_inscricao(self):
        recipes.candidato.make(
            user=self.usuario_base
        )
        modelo_questionario = recipes.modelo_questionario.make()
        recipes.processo_inscricao.make(
            edital=modelo_questionario.edital,
        )
        self.client.login(**self.usuario_base.credentials)
        response = self.client.get(
            reverse("responder_questionario_psct", args=[modelo_questionario.edital_id])
        )
        self.assertEqual(200, response.status_code)
