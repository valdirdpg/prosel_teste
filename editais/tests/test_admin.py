import datetime
from unittest import mock

from django.contrib.admin import AdminSite
from django.test import RequestFactory, TestCase

from . import recipes
from .. import admin
from .. import models


class EditalAdminTestCase(TestCase):
    def setUp(self):
        super().setUp()
        site = AdminSite()
        self.admin = admin.EditalAdmin(models.Edital, site)
        request_factory = RequestFactory()
        self.request = request_factory.get("/admin")

    def test_get_readonly_fields_deveria_retornar_a_lista_de_campos_nao_editaveis(self):
        obj = mock.Mock()
        self.assertListEqual(
            ["numero", "ano", "data_publicacao", "retificado"],
            self.admin.get_readonly_fields(self.request, obj),
        )

    def test_get_readonly_fields_deveria_retornar_uma_lista_vazia_quando_obj_nao_for_passado(
        self
    ):
        self.assertTupleEqual((), self.admin.get_readonly_fields(self.request))

    def test_fieldsets_devem_ser_personalizados_quando_edital_for_retificado(self):
        edital = recipes.edital.make(retificado=recipes.edital.make())
        expected = (
            (
                "Identificação",
                {
                    "fields": (
                        ("nome"),
                        ("numero", "ano", "data_publicacao"),
                        ("tipo"),
                        ("retificado"),
                        ("publicado"),
                    )
                },
            ),
        )
        self.assertEqual(expected, self.admin.get_fieldsets(self.request, edital))

    def test_fieldsets_devem_ser_personalizados_quando_retificado_for_passado_via_http_get(
        self
    ):
        self.request.GET = {"retificado": "1"}
        expected = (
            (
                "Identificação",
                {
                    "fields": (
                        ("nome"),
                        ("numero", "ano", "data_publicacao"),
                        ("tipo"),
                        ("retificado"),
                        ("publicado"),
                    )
                },
            ),
        )
        self.assertEqual(self.admin.get_fieldsets(self.request), expected)

    def test_save_model_deveria_alterar_dados_basicos_do_edital_retificado(self):
        edital_abertura = recipes.edital.make()
        edital_retificacao = recipes.edital.make()
        self.request.GET = {"retificado": edital_abertura.id}
        self.admin.save_model(self.request, edital_retificacao, None, None)
        self.assertEqual(edital_retificacao.edicao, edital_abertura.edicao)
        self.assertEqual(
            edital_retificacao.setor_responsavel, edital_abertura.setor_responsavel
        )
        self.assertEqual(edital_retificacao.descricao, edital_abertura.descricao)
        self.assertEqual(
            edital_retificacao.prazo_pagamento, edital_abertura.prazo_pagamento
        )
        self.assertEqual(
            edital_retificacao.link_inscricoes, edital_abertura.link_inscricoes
        )

    def test_save_related_deveria_criar_o_periodo_de_inscricao(self):
        form = mock.Mock()
        form.cleaned_data = {
            "inscricao_inicio": datetime.date.today(),
            "inscricao_fim": datetime.date.today(),
        }
        edital = recipes.edital.make()
        form.instance = edital
        self.admin.save_related(self.request, form, [], None)
        self.assertTrue(edital.cronogramas_selecao.filter(inscricao=True).exists())

    def test_save_related_deveria_atualizar_o_periodo_de_inscricao(self):
        form = mock.Mock()
        nova_data = datetime.date.today() + datetime.timedelta(days=1)
        form.cleaned_data = {"inscricao_inicio": nova_data, "inscricao_fim": nova_data}
        periodo = recipes.periodo_selecao.make(inscricao=True)
        edital = periodo.edital
        form.instance = edital
        self.admin.save_related(self.request, form, [], None)
        periodo.refresh_from_db()
        self.assertEqual(nova_data, periodo.inicio)
        self.assertEqual(nova_data, periodo.fim)


class PeriodoSelecaoInlineTestCase(TestCase):
    def setUp(self):
        super().setUp()
        site = AdminSite()
        self.admin = admin.PeriodoSelecaoInline(models.Edital, site)
        request_factory = RequestFactory()
        self.request = request_factory.get("/admin")
        self.request.user = mock.Mock()

    def test_get_queryset_deveria_excluir_os_periodos_inscricao(self):
        periodo = recipes.periodo_selecao.make(inscricao=True)
        self.assertNotIn(periodo, self.admin.get_queryset(self.request))
