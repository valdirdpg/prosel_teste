from unittest import mock

from django.contrib.admin import AdminSite
from django.test import RequestFactory, TestCase
from django.urls import reverse

import base.tests.recipes
import editais.tests.recipes
from .. import recipes
from ... import models
from ...admin import analise as admin


class FaseAnaliseTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.admin = admin.FaseAnaliseAdmin(models.FaseAnalise, AdminSite())

    def test_acoes_deve_retornar_html_de_botao_de_gerar_resultado(self):
        obj = mock.Mock()
        obj.pk = 1
        url = reverse("resultado_preliminar_psct", kwargs=dict(fase_pk=obj.pk))
        html = f'<a href="{url}" class="btn btn-default btn-xs">Gerar resultado preliminar</a>'
        self.assertEqual(html, self.admin.acoes(obj))

    def test_edital_display_deve_retornar_numero_e_ano_do_edital(self):
        edital = editais.tests.recipes.edital.make()
        obj = mock.Mock()
        obj.edital = edital
        self.assertEqual(f"{edital.numero}/{edital.ano}", self.admin.edital_display(obj))


class AvaliacaoAvaliadorTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.admin = admin.AvaliacaoAvaliadorAdmin(models.AvaliacaoAvaliador, AdminSite())

    def test_situacao_display_deve_retornar_get_situacao_display_do_objeto(self):
        obj = mock.Mock()
        obj.get_situacao_display.return_value = "Expected value"
        self.assertEqual("Expected value", self.admin.situacao_display(obj))

    def test_concluida_display_deve_retornar_get_concluida_display_do_objeto(self):
        obj = mock.Mock()
        obj.get_concluida_display.return_value = "Expected value"
        self.assertEqual("Expected value", self.admin.concluida_display(obj))

    def test_avaliador_display_deve_retornar_nome_e_username_do_avaliador(self):
        obj = mock.Mock()
        obj.avaliador = base.tests.recipes.user.make()
        self.assertEqual(
            f"{obj.avaliador.get_full_name()} ({obj.avaliador.username})",
            self.admin.avaliador_display(obj)
        )

    def test_candidato_deve_retornar_candidato_da_inscricao_avaliada(self):
        candidato = recipes.candidato.make()
        obj = mock.Mock()
        obj.inscricao.candidato = candidato
        self.assertEqual(candidato, self.admin.candidato(obj))

    def test_has_add_permission(self):
        request = RequestFactory().get("/admin")
        request.user = mock.Mock()
        self.assertFalse(self.admin.has_add_permission(request))

    def test_has_delete_permission(self):
        request = RequestFactory().get("/admin")
        request.user = mock.Mock()
        self.assertFalse(self.admin.has_delete_permission(request))
