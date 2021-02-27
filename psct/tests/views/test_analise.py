from unittest import mock

from django.contrib.messages.storage import default_storage
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import override_settings, RequestFactory, TestCase
from django.urls import reverse

import base.tests.recipes
from .. import mixins
from .. import recipes
from ... import permissions
from ...forms.recurso import RedistribuirForm
from ...views import analise as views
from base.tests.mixins import UserTestMixin


class ImportarInscricaoViewTestCase(UserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.AdministradoresPSCT().sync()
        permissions.AvaliadorPSCT().sync()
        cls.fase_analise = recipes.fase_analise.make()
        cls.url = reverse("analise_importar_inscricao_psct", args=[cls.fase_analise.id])
        cls.request = RequestFactory().get(cls.url)
        cls.request.user = cls.usuario_base
        permissions.AdministradoresPSCT.add_user(cls.usuario_base)
        cls.view = views.ImportarInscricaoView()
        cls.view.setup(cls.request, fase_pk=cls.fase_analise.id)

    def test_title(self):
        self.client.login(**self.usuario_base.credentials)
        response = self.client.get(self.url)
        title = f"Deseja importar inscrições do edital {self.fase_analise.edital} para análise?"
        self.assertContains(response, title)

    def test_get_context_data_deve_lancar_404_se_fase_nao_existe(self):
        view = views.ImportarInscricaoView()
        view.setup(self.request, fase_pk=-1)
        with self.assertRaises(Http404):
            view.get_context_data()

    def test_get_context_data_deve_conter_o_titulo_da_pagina(self):
        context = self.view.get_context_data()
        self.assertEqual(
            f"Deseja importar inscrições do edital {self.fase_analise.edital} para análise?",
            context["titulo"]
        )

    def test_get_context_data_deve_conter_url_de_voltar_para_listagem_de_inscricoes(self):
        context = self.view.get_context_data()
        self.assertIn("back_url", context)
        self.assertEqual(reverse("list_inscricao_psct"), context["back_url"])

    def test_get_context_data_deve_conter_o_breadcrumb_da_pagina(self):
        context = self.view.get_context_data()
        self.assertIn("breadcrumb", context)
        self.assertIn(("Inscrições", reverse("list_inscricao_psct")), context["breadcrumb"])
        self.assertIn(("Importar Inscrições", ""), context["breadcrumb"])

    @override_settings(CELERY_ALWAYS_EAGER=True)
    @mock.patch("psct.tasks.analise.importar")
    def test_form_valid_deve_conter_a_mensagem_de_sucesso_configurada(self, importar):
        self.client.login(**self.usuario_base.credentials)
        response = self.client.post(
            reverse("analise_importar_inscricao_psct", args=[self.fase_analise.pk]), follow=True
        )
        response_messages = list(map(lambda x: x.message, response.context.get('messages')))
        self.assertIn("Processo de importação iniciado com sucesso", response_messages)

    def test_template_deve_estar_corretamente_configurado(self):
        self.assertEqual("psct/base/confirmacao.html", self.view.template_name)


class RedistribuirInscricaoAvaliacaoViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.AvaliadorPSCT().sync()
        cls.fase_analise = recipes.fase_analise.make()
        cls.view_url = reverse("redistribuir_inscricao_avaliador_psct", args=[cls.fase_analise.id])
        cls.request = RequestFactory().get(cls.view_url)
        cls.request.user = mock.Mock()
        cls.view = views.RedistribuirInscricaoView()
        cls.view.setup(cls.request, fase_pk=cls.fase_analise.id)

    def test_setup_deve_lancar_404_se_fase_nao_existe(self):
        view = views.RedistribuirInscricaoView()
        with self.assertRaises(Http404):
            view.setup(self.request, fase_pk=999)

    def test_get_context_data_deve_conter_o_titulo_da_pagina(self):
        context = self.view.get_context_data()
        self.assertEqual(f"Redistribuir Inscrições", context["titulo"])

    def test_get_context_data_deve_conter_o_breadcrumb_da_pagina(self):
        context = self.view.get_context_data()
        self.assertIn("breadcrumb", context)
        self.assertIn(("Inscrições", reverse("list_inscricao_psct")), context["breadcrumb"])
        self.assertIn(("Redistribuir Inscrição", ""), context["breadcrumb"])

    def test_form_kwargs_deve_conter_a_fase(self):
        kwargs = self.view.get_form_kwargs()
        self.assertIn("fase", kwargs)
        self.assertEqual(self.fase_analise, kwargs["fase"])

    @mock.patch("psct.forms.recurso.RedistribuirForm.redistribuir")
    def test_form_valid_deve_adicionar_mensagem_de_sucesso(self, redistribuir):
        INSCRICOES_A_REDISTRIBUIR = 1
        redistribuir.return_value = INSCRICOES_A_REDISTRIBUIR
        request = RequestFactory().get(self.view_url)
        request.session = {}
        view = views.RedistribuirInscricaoView()
        view.setup(request, fase_pk=self.fase_analise.id)
        storage = default_storage(request)
        request._messages = storage
        view.form_valid(RedistribuirForm(fase=self.fase_analise))
        self.assertTrue(storage.added_new)
        self.assertIn(
            f"{INSCRICOES_A_REDISTRIBUIR} inscrições foram redistribuídas com sucesso",
            [m.message for m in storage]
        )

    def test_template_deve_estar_corretamente_configurado(self):
        self.assertEqual("psct/base/display_form.html", self.view.template_name)


class RegraExclusaoViewTestCase(mixins.AdministradorPSCTTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.AvaliadorPSCT().sync()
        cls.fase_analise = recipes.fase_analise.make()
        cls.view_url = reverse("regra_exclusao_inscricao_psct", args=[cls.fase_analise.id])
        cls.request = RequestFactory().get(cls.view_url)
        cls.request.user = cls.usuario_administrador
        cls.view = views.RegraExclusaoView()
        cls.view.setup(cls.request, fase_pk=cls.fase_analise.id)

    def test_get_context_data_deve_conter_o_titulo_da_pagina(self):
        context = self.view.get_context_data()
        self.assertEqual("Regra de Permissão para Análise", context["titulo"])

    def test_get_context_data_deve_conter_o_breadcrumb_da_pagina(self):
        context = self.view.get_context_data()
        self.assertIn("breadcrumb", context)
        self.assertIn(("Inscrições", reverse("list_inscricao_psct")), context["breadcrumb"])
        self.assertIn(("Regra de Permissão para Análise", ""), context["breadcrumb"])

    def test_has_permission_deve_retornar_false_se_usuario_nao_estah_no_group_required(self):
        request = RequestFactory().get(self.view_url)
        request.user = base.tests.recipes.user.make()
        view = views.RegraExclusaoView()
        view.setup(request, fase_pk=self.fase_analise.id)
        self.assertFalse(view.has_permission())

    def test_has_permission_deve_lancar_404_se_fase_nao_existe(self):
        view = views.RegraExclusaoView()
        view.setup(self.request, fase_pk=999)
        with self.assertRaises(Http404):
            view.has_permission()

    @mock.patch("psct.models.analise.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    def test_has_permission_deve_retornar_falso_se_fase_nao_estiver_vigente(self, acontecendo):
        acontecendo.return_value = False
        self.assertFalse(self.view.has_permission())

    @mock.patch("psct.models.analise.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    def test_has_permission_deve_retornar_verdadeiro_quando_fase_estiver_vigente(self, acontecendo):
        acontecendo.return_value = True
        self.assertTrue(self.view.has_permission())

    def test_template_deve_estar_corretamente_configurado(self):
        self.assertEqual("psct/base/display_form.html", self.view.template_name)


class GrupoRegraExclusaoViewTestCase(mixins.AdministradorPSCTTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.AvaliadorPSCT().sync()
        cls.fase_analise = recipes.fase_analise.make()
        cls.coluna = recipes.coluna.make()
        cls.view_url = reverse(
            "grupo_regra_exclusao_inscricao_psct", args=[cls.fase_analise.id, cls.coluna.id]
        )
        cls.request = RequestFactory().get(cls.view_url)
        cls.request.user = cls.usuario_administrador
        cls.view = views.GrupoRegraExclusaoView()
        cls.view.setup(cls.request, fase_pk=cls.fase_analise.id, coluna_pk=cls.coluna.id)

    @mock.patch("django.views.generic.FormView.get_context_data")
    def test_get_context_data_deve_conter_o_titulo_da_pagina(self, get_context_data):
        get_context_data.return_value = {}
        context = self.view.get_context_data()
        self.assertIn("titulo", context)
        self.assertEqual("Definir Grupos de Exclusão", context["titulo"])

    @mock.patch("django.views.generic.FormView.get_context_data")
    def test_get_context_data_deve_conter_o_breadcrumb_da_pagina(self, get_context_data):
        get_context_data.return_value = {}
        context = self.view.get_context_data()
        self.assertIn("breadcrumb", context)
        self.assertIn(("Inscrições", reverse("list_inscricao_psct")), context["breadcrumb"])
        self.assertIn(("Definir Grupos de Exclusão", ""), context["breadcrumb"])

    def test_has_permission_deve_retornar_false_se_usuario_nao_estah_no_group_required(self):
        request = RequestFactory().get(self.view_url)
        request.user = base.tests.recipes.user.make()
        view = views.GrupoRegraExclusaoView()
        view.setup(request, fase_pk=self.fase_analise.id, coluna_pk=self.coluna.id)
        self.assertFalse(view.has_permission())

    def test_has_permission_deve_lancar_404_se_fase_nao_existe(self):
        view = views.GrupoRegraExclusaoView()
        view.setup(self.request, fase_pk=0, coluna_pk=self.coluna.id)
        with self.assertRaises(Http404):
            view.has_permission()

    def test_has_permission_deve_lancar_404_se_coluna_nao_existe(self):
        view = views.GrupoRegraExclusaoView()
        view.setup(self.request, fase_pk=self.fase_analise.id, coluna_pk=0)
        with self.assertRaises(Http404):
            view.has_permission()

    @mock.patch("psct.models.analise.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    def test_has_permission_deve_retornar_false_se_fase_nao_estiver_vigente(self, acontecendo):
        acontecendo.return_value = False
        self.assertFalse(self.view.has_permission())

    @mock.patch("psct.models.analise.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    def test_has_permission_deve_retornar_false_se_fase_estiver_vigente(self, acontecendo):
        acontecendo.return_value = True
        self.assertTrue(self.view.has_permission())

    def test_form_kwargs_deve_conter_a_fase(self):
        kwargs = self.view.get_form_kwargs()
        self.assertIn("fase", kwargs)
        self.assertEqual(self.fase_analise, kwargs["fase"])

    def test_form_kwargs_deve_conter_a_coluna(self):
        kwargs = self.view.get_form_kwargs()
        self.assertIn("coluna", kwargs)
        self.assertEqual(self.coluna, kwargs["coluna"])

    def test_template_deve_estar_corretamente_configurado(self):
        self.assertEqual("psct/base/display_form.html", self.view.template_name)


class CreateLoteAvaliadorInscricaoViewTestCase(
    UserTestMixin,
    mixins.FaseAnaliseTestData,
    mixins.ProcessoInscricaoMixin,
    TestCase
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.AvaliadorPSCT().sync()
        permissions.AvaliadorPSCT.add_user(cls.usuario_base)
        cls.grupo_avaliadores.grupo.user_set.add(cls.usuario_base)
        cls.quantidade_inscricoes = 5

        cls.view_url = reverse(
            "add_lote_avaliador_inscricao_psct",
            args=[cls.fase_analise.id, cls.quantidade_inscricoes]
        )
        cls.request = RequestFactory().get(cls.view_url)
        cls.request.user = cls.usuario_base

        cls.view = views.CreateLoteAvaliadorInscricaoView()
        cls.view.setup(
            cls.request,
            fase_pk=cls.fase_analise.id,
            quantidade=cls.quantidade_inscricoes
        )

    def test_get_context_data_deve_conter_o_titulo_da_pagina(self):
        context = self.view.get_context_data()
        self.assertEqual(
            f"Deseja obter {self.quantidade_inscricoes} inscrições para análise?",
            context["titulo"]
        )

    def test_get_context_data_deve_conter_url_de_voltar_para_listagem_de_inscricoes(self):
        context = self.view.get_context_data()
        self.assertIn("back_url", context)
        self.assertEqual(reverse("list_inscricao_psct"), context["back_url"])

    def test_get_context_data_deve_conter_o_breadcrumb_da_pagina(self):
        context = self.view.get_context_data()
        self.assertIn("breadcrumb", context)
        self.assertIn(("Inscrições", reverse("list_inscricao_psct")), context["breadcrumb"])
        self.assertIn(("Obter Inscrições", ""), context["breadcrumb"])

    @mock.patch("psct.models.analise.get_lote_avaliador")
    def test_form_valid_deve_conter_a_mensagem_de_sucesso_configurada(self, get_lote_avaliador):
        get_lote_avaliador.return_value = self.quantidade_inscricoes
        self.client.login(**self.usuario_base.credentials)
        url = reverse(
            "add_lote_avaliador_inscricao_psct",
            args=[self.fase_analise.pk, self.quantidade_inscricoes]
        )
        response = self.client.post(url, follow=True)
        response_messages = list(map(lambda x: x.message, response.context.get('messages')))
        self.assertIn(
            f"Foram adicionadas {self.quantidade_inscricoes} inscrições em sua caixa de avaliação",
            response_messages
        )

    def test_requisicao_get_deve_lancar_404_se_quantidade_for_diferente_de_lote_padrao(self):
        self.client.login(**self.usuario_base.credentials)
        url = reverse(
            "add_lote_avaliador_inscricao_psct",
            args=[self.fase_analise.pk, self.quantidade_inscricoes + 1]
        )
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)

    def test_has_permission_deve_retornar_false_se_usuario_nao_eh_avaliador(self):
        request = RequestFactory().get(self.view_url)
        request.user = base.tests.recipes.user.make()
        view = views.CreateLoteAvaliadorInscricaoView()
        view.setup(request, fase_pk=self.fase_analise.id, quantidade=self.quantidade_inscricoes)
        self.assertFalse(view.has_permission())

    def test_has_permission_deve_lancar_404_se_fase_nao_existe(self):
        view = views.CreateLoteAvaliadorInscricaoView()
        view.setup(self.request, fase_pk=999, quantidade=self.quantidade_inscricoes)
        with self.assertRaises(Http404):
            view.has_permission()

    def test_has_permission_deve_retornar_false_se_usuario_nao_eh_avaliador_da_fase(self):
        request = RequestFactory().get(self.view_url)
        request.user = base.tests.recipes.user.make()
        permissions.AvaliadorPSCT.add_user(request.user)
        view = views.CreateLoteAvaliadorInscricaoView()
        view.setup(request, fase_pk=self.fase_analise.id, quantidade=self.quantidade_inscricoes)
        self.assertFalse(view.has_permission())

    @mock.patch("psct.models.analise.MailBoxAvaliadorInscricao.possui_inscricao_pendente")
    def test_has_permission_deve_retornar_false_se_avaliador_tem_avaliacao_pendente(
            self,
            possui_inscricao_pendente
    ):
        possui_inscricao_pendente.return_value = True
        self.assertFalse(self.view.has_permission())

    @mock.patch("psct.models.analise.MailBoxAvaliadorInscricao.possui_inscricao_pendente")
    def test_has_permission_deve_retornar_true_se_avaliador_nao_tem_avaliacao_pendente(
            self,
            possui_inscricao_pendente
    ):
        possui_inscricao_pendente.return_value = False
        self.assertTrue(self.view.has_permission())

    def test_template_deve_estar_corretamente_configurado(self):
        self.assertEqual("psct/base/confirmacao.html", self.view.template_name)


class CreateLoteHomologadorInscricaoViewTestCase(
    UserTestMixin,
    mixins.FaseAnaliseTestData,
    mixins.ProcessoInscricaoMixin,
    TestCase
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.HomologadorPSCT.add_user(cls.usuario_base)
        cls.grupo_homologadores.grupo.user_set.add(cls.usuario_base)
        cls.quantidade_inscricoes = 5

        cls.view_url = reverse(
            "add_lote_homologador_inscricao_psct",
            args=[cls.fase_analise.id, cls.quantidade_inscricoes]
        )
        cls.request = RequestFactory().get(cls.view_url)
        cls.request.user = cls.usuario_base

        cls.view = views.CreateLoteHomologadorInscricaoView()
        cls.view.setup(
            cls.request,
            fase_pk=cls.fase_analise.id,
            quantidade=cls.quantidade_inscricoes
        )

    def test_get_context_data_deve_conter_o_titulo_da_pagina(self):
        context = self.view.get_context_data()
        self.assertEqual(
            f"Deseja obter {self.quantidade_inscricoes} inscrições para homologação?",
            context["titulo"]
        )

    def test_get_context_data_deve_conter_url_de_voltar_para_listagem_de_inscricoes(self):
        context = self.view.get_context_data()
        self.assertIn("back_url", context)
        self.assertEqual(reverse("list_inscricao_psct"), context["back_url"])

    def test_get_context_data_deve_conter_o_breadcrumb_da_pagina(self):
        context = self.view.get_context_data()
        self.assertIn("breadcrumb", context)
        self.assertIn(("Inscrições", reverse("list_inscricao_psct")), context["breadcrumb"])
        self.assertIn(("Obter Inscrições", ""), context["breadcrumb"])

    @mock.patch("psct.models.analise.get_lote_homologador")
    def test_form_valid_deve_conter_a_mensagem_de_sucesso_configurada(self, get_lote_homologador):
        get_lote_homologador.return_value = self.quantidade_inscricoes
        self.client.login(**self.usuario_base.credentials)
        url = reverse(
            "add_lote_homologador_inscricao_psct",
            args=[self.fase_analise.pk, self.quantidade_inscricoes]
        )
        response = self.client.post(url, follow=True)
        response_messages = list(map(lambda x: x.message, response.context.get('messages')))
        self.assertIn(
            (
                f"Foram adicionadas {self.quantidade_inscricoes} inscrições "
                f"em sua caixa de homologação"
            ),
            response_messages
        )

    def test_requisicao_get_deve_lancar_404_se_quantidade_for_diferente_de_lote_padrao(self):
        self.client.login(**self.usuario_base.credentials)
        url = reverse(
            "add_lote_homologador_inscricao_psct",
            args=[self.fase_analise.pk, self.quantidade_inscricoes + 1]
        )
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)

    def test_has_permission_deve_retornar_false_se_usuario_nao_eh_homologador(self):
        request = RequestFactory().get(self.view_url)
        request.user = base.tests.recipes.user.make()
        view = views.CreateLoteHomologadorInscricaoView()
        view.setup(request, fase_pk=self.fase_analise.id, quantidade=self.quantidade_inscricoes)
        self.assertFalse(view.has_permission())

    def test_has_permission_deve_lancar_404_se_fase_nao_existe(self):
        view = views.CreateLoteHomologadorInscricaoView()
        view.setup(self.request, fase_pk=999, quantidade=self.quantidade_inscricoes)
        with self.assertRaises(Http404):
            view.has_permission()

    def test_has_permission_deve_retornar_false_se_usuario_nao_eh_homologador_da_fase(self):
        request = RequestFactory().get(self.view_url)
        request.user = base.tests.recipes.user.make()
        permissions.HomologadorPSCT.add_user(request.user)
        view = views.CreateLoteHomologadorInscricaoView()
        view.setup(request, fase_pk=self.fase_analise.id, quantidade=self.quantidade_inscricoes)
        self.assertFalse(view.has_permission())

    @mock.patch("psct.models.analise.MailBoxHomologadorInscricao.possui_inscricao_pendente")
    def test_has_permission_deve_retornar_false_se_homologador_tem_homologacao_pendente(
            self,
            possui_inscricao_pendente
    ):
        possui_inscricao_pendente.return_value = True
        self.assertFalse(self.view.has_permission())

    @mock.patch("psct.models.analise.MailBoxHomologadorInscricao.possui_inscricao_pendente")
    def test_has_permission_deve_retornar_true_se_homologador_nao_tem_homologacao_pendente(
            self,
            possui_inscricao_pendente
    ):
        possui_inscricao_pendente.return_value = False
        self.assertTrue(self.view.has_permission())

    def test_template_deve_estar_corretamente_configurado(self):
        self.assertEqual("psct/base/confirmacao.html", self.view.template_name)


class CreateAvaliacaoAvaliadorInscricaoViewTestCase(
    mixins.AvaliadorPSCTTestData,
    mixins.InscricaoPreAnaliseTestData,
    mixins.EditalTestData,
    mixins.CursoTestData,
    TestCase
):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view_url = reverse("add_avaliacao_avaliador_inscricao_psct", args=[cls.inscricao.pk])
        cls.request = RequestFactory().get(cls.view_url)
        cls.request.user = cls.usuario_avaliador
        cls.view = views.CreateAvaliacaoAvaliadorInscricaoView()
        cls.view.setup(cls.request, inscricao_pk=cls.inscricao.id)
        cls.view.object = None

    def test_has_permission_deve_lancar_permission_denied_se_inscricao_nao_existir(self):
        view = views.CreateAvaliacaoAvaliadorInscricaoView()
        view.setup(self.request, inscricao_pk=0)
        with self.assertRaises(PermissionDenied):
            view.has_permission()

    def test_has_permission_deve_retornar_false_se_usuario_nao_estah_no_grupo_avaliador(self):
        request = RequestFactory().get(self.view_url)
        request.user = base.tests.recipes.user.make()
        view = views.CreateAvaliacaoAvaliadorInscricaoView()
        view.setup(request, inscricao_pk=self.inscricao.id)
        self.assertFalse(view.has_permission())

    def test_has_permission_deve_retornar_falso_se_total_avaliacoes_for_maior_que_exigido_na_fase(
            self
    ):
        recipes.avaliacao_avaliador.make(inscricao=self.inscricao)
        self.assertFalse(self.view.has_permission())

    def test_has_permission_deve_retornar_false_se_inscricao_nao_estiver_em_mailbox_avaliador(self):
        mailbox_avaliador = recipes.mailbox_avaliador_inscricao.make(
            avaliador=self.usuario_avaliador
        )
        self.assertNotIn(self.inscricao, mailbox_avaliador.inscricoes.all())
        self.assertFalse(self.view.has_permission())

    def test_has_permission_deve_retornar_false_se_avaliador_já_tiver_avaliado_a_mesma_inscricao(
            self
    ):
        recipes.mailbox_avaliador_inscricao.make(
            avaliador=self.usuario_avaliador,
            inscricoes=[self.inscricao]
        )
        recipes.avaliacao_avaliador.make(inscricao=self.inscricao, avaliador=self.usuario_avaliador)
        self.assertFalse(self.view.has_permission())

    @mock.patch("psct.models.analise.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    def test_has_permission_deve_retornar_false_se_fase_analise_nao_estiver_vigente(
            self, acontecendo
    ):
        acontecendo.return_value = False
        mailbox_avaliador = recipes.mailbox_avaliador_inscricao.make(
            avaliador=self.usuario_avaliador
        )
        mailbox_avaliador.inscricoes.add(self.inscricao)
        self.assertFalse(self.view.has_permission())

    @mock.patch("psct.models.analise.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    def test_has_permission_deve_retornar_true_se_inscricao_nao_avaliada_esta_na_box_e_fase_vigente(
            self, acontecendo
    ):
        acontecendo.return_value = True
        mailbox_avaliador = recipes.mailbox_avaliador_inscricao.make(
            avaliador=self.usuario_avaliador
        )
        mailbox_avaliador.inscricoes.add(self.inscricao)
        self.assertTrue(self.view.has_permission())

    def test_form_kwargs_deve_conter_inscricao(self):
        kwargs = self.view.get_form_kwargs()
        self.assertIn("inscricao", kwargs)
        self.assertEqual(self.inscricao, kwargs["inscricao"])

    def test_get_context_data_deve_conter_o_titulo_da_pagina(self):
        context = self.view.get_context_data()
        self.assertEqual(f"Avaliação da {self.inscricao_original}", context["titulo"])

    def test_get_context_data_deve_conter_inscricao_pre_analise(self):
        context = self.view.get_context_data()
        self.assertIn("inscricao", context)
        self.assertEqual(self.inscricao, context["inscricao"])

    def test_get_context_data_deve_conter_inscricao_original(self):
        context = self.view.get_context_data()
        self.assertIn("inscricao_original", context)
        self.assertEqual(self.inscricao_original, context["inscricao_original"])

    def test_get_context_data_deve_conter_o_breadcrumb_da_pagina(self):
        context = self.view.get_context_data()
        self.assertIn("breadcrumb", context)
        self.assertIn(("Inscrições", reverse("list_inscricao_psct")), context["breadcrumb"])
        self.assertIn(("Avaliar inscrição", ""), context["breadcrumb"])


class UpdateAvaliacaoAvaliadorInscricaoViewTestCase(
    mixins.AvaliadorPSCTTestData,
    mixins.InscricaoPreAnaliseTestData,
    mixins.EditalTestData,
    mixins.CursoTestData,
    TestCase
):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.avaliacao = recipes.avaliacao_avaliador.make(inscricao=cls.inscricao)
        cls.view_url = reverse("change_avaliacao_avaliador_inscricao_psct", args=[cls.avaliacao.pk])
        cls.request = RequestFactory().get(cls.view_url)
        cls.request.user = cls.usuario_avaliador
        cls.view = views.UpdateAvaliacaoAvaliadorInscricaoView()
        cls.view.setup(cls.request, pk=cls.avaliacao.id)
        cls.view.object = None

    def test_has_permission_deve_retornar_false_se_usuario_nao_estah_no_group_required(self):
        request = RequestFactory().get(self.view_url)
        request.user = base.tests.recipes.user.make()
        view = views.UpdateAvaliacaoAvaliadorInscricaoView()
        view.setup(request, pk=self.avaliacao.id)
        self.assertFalse(self.view.has_permission())

    def test_has_permission_deve_lancar_permission_denied_se_avaliacao_nao_existir(self):
        view = views.UpdateAvaliacaoAvaliadorInscricaoView()
        view.setup(self.request, pk=0)
        with self.assertRaises(PermissionDenied):
            view.has_permission()

    @mock.patch("psct.models.analise.AvaliacaoAvaliador.pode_alterar")
    def test_has_permission_deve_retornar_false_se_avaliador_nao_pode_alterar_avaliacao(
            self, pode_alterar
    ):
        pode_alterar.return_value = False
        self.assertFalse(self.view.has_permission())

    @mock.patch("psct.models.analise.AvaliacaoAvaliador.pode_alterar")
    def test_has_permission_deve_retornar_true_se_avaliador_pode_alterar_avaliacao(
            self, pode_alterar
    ):
        pode_alterar.return_value = True
        self.assertTrue(self.view.has_permission())

    def test_form_kwargs_deve_conter_inscricao(self):
        kwargs = self.view.get_form_kwargs()
        self.assertIn("inscricao", kwargs)
        self.assertEqual(self.inscricao, kwargs["inscricao"])

    def test_get_context_data_deve_conter_o_titulo_da_pagina(self):
        context = self.view.get_context_data()
        self.assertEqual(f"Avaliação da {self.inscricao_original}", context["titulo"])

    def test_get_context_data_deve_conter_inscricao_pre_analise(self):
        context = self.view.get_context_data()
        self.assertIn("inscricao", context)
        self.assertEqual(self.inscricao, context["inscricao"])

    def test_get_context_data_deve_conter_inscricao_original(self):
        context = self.view.get_context_data()
        self.assertIn("inscricao_original", context)
        self.assertEqual(self.inscricao_original, context["inscricao_original"])

    def test_get_context_data_deve_conter_o_breadcrumb_da_pagina(self):
        context = self.view.get_context_data()
        self.assertIn("breadcrumb", context)
        self.assertIn(("Inscrições", reverse("list_inscricao_psct")), context["breadcrumb"])
        self.assertIn(("Avaliar inscrição", ""), context["breadcrumb"])

    def test_form_invalid_deve_adicionar_mensagem_de_erro(self):
        request = RequestFactory().get(self.view_url)
        request.user = self.usuario_avaliador
        request.session = {}
        storage = default_storage(request)
        request._messages = storage
        view = views.UpdateAvaliacaoAvaliadorInscricaoView()
        view.setup(request, pk=self.avaliacao.id)
        view.object = None
        view.form_invalid(mock.Mock())
        self.assertTrue(storage.added_new)
        self.assertIn(
            "Por favor, corrija os erros abaixo para continuar.", [m.message for m in storage]
        )


class AvaliacaoAvaliadorViewTestCase(
    mixins.AvaliadorPSCTTestData,
    mixins.InscricaoPreAnaliseTestData,
    mixins.EditalTestData,
    mixins.CursoTestData,
    TestCase
):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.avaliacao = recipes.avaliacao_avaliador.make(inscricao=cls.inscricao)
        cls.view_url = reverse("view_avaliacao_avaliador_inscricao_psct", args=[cls.avaliacao.id])
        cls.request = RequestFactory().get(cls.view_url)
        cls.request.user = cls.usuario_avaliador
        cls.view = views.AvaliacaoAvaliadorView()
        cls.view.setup(cls.request, pk=cls.avaliacao.id)
        cls.view.object = None

    def test_has_permission_deve_retornar_false_se_usuario_nao_estah_no_group_required(self):
        request = RequestFactory().get(self.view_url)
        request.user = base.tests.recipes.user.make()
        view = views.AvaliacaoAvaliadorView()
        view.setup(request, pk=self.avaliacao.id)
        self.assertFalse(self.view.has_permission())

    def test_has_permission_deve_lancar_permission_denied_se_avaliacao_nao_existir(self):
        view = views.AvaliacaoAvaliadorView()
        view.setup(self.request, pk=0)
        with self.assertRaises(PermissionDenied):
            view.has_permission()

    @mock.patch("psct.models.analise.AvaliacaoAvaliador.is_owner")
    def test_has_permission_deve_retornar_false_se_avaliador_nao_eh_dono_da_avaliacao(
            self, is_owner
    ):
        is_owner.return_value = False
        self.assertFalse(self.view.has_permission())

    @mock.patch("psct.models.analise.AvaliacaoAvaliador.is_owner")
    def test_has_permission_deve_retornar_true_se_avaliador_eh_dono_da_avaliacao(
            self, is_owner
    ):
        is_owner.return_value = True
        self.assertTrue(self.view.has_permission())

    def test_get_context_data_deve_conter_o_titulo_da_pagina(self):
        context = self.view.get_context_data()
        self.assertEqual(f"Avaliação da {self.inscricao_original}", context["titulo"])

    def test_get_context_data_deve_conter_inscricao_pre_analise(self):
        context = self.view.get_context_data()
        self.assertIn("inscricao", context)
        self.assertEqual(self.inscricao, context["inscricao"])

    def test_get_context_data_deve_conter_inscricao_original(self):
        context = self.view.get_context_data()
        self.assertIn("inscricao_original", context)
        self.assertEqual(self.inscricao_original, context["inscricao_original"])

    def test_get_context_data_deve_conter_o_breadcrumb_da_pagina(self):
        context = self.view.get_context_data()
        self.assertIn("breadcrumb", context)
        self.assertIn(("Inscrições", reverse("list_inscricao_psct")), context["breadcrumb"])
        self.assertIn((f"Avaliação #{self.avaliacao.id}", ""), context["breadcrumb"])


class CreateAvaliacaoHomologadorInscricaoViewTestCase(
    mixins.HomologadorPSCTTestData,
    mixins.InscricaoPreAnaliseTestData,
    mixins.EditalTestData,
    mixins.CursoTestData,
    TestCase
):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view_url = reverse("add_avaliacao_homologador_inscricao_psct", args=[cls.inscricao.id])
        cls.request = RequestFactory().get(cls.view_url)
        cls.request.user = cls.usuario_homologador
        cls.view = views.CreateAvaliacaoHomologadorInscricaoView()
        cls.view.setup(cls.request, inscricao_pk=cls.inscricao.id)
        cls.view.object = None

    def test_has_permission_deve_lancar_permission_denied_se_inscricao_nao_existir(self):
        view = views.CreateAvaliacaoHomologadorInscricaoView()
        view.setup(self.request, inscricao_pk=0)
        with self.assertRaises(PermissionDenied):
            view.has_permission()

    def test_has_permission_deve_retornar_false_se_usuario_nao_estah_no_grupo_homologador(self):
        request = RequestFactory().get(self.view_url)
        request.user = base.tests.recipes.user.make()
        view = views.CreateAvaliacaoHomologadorInscricaoView()
        view.setup(request, inscricao_pk=self.inscricao.id)
        self.assertFalse(view.has_permission())

    def test_has_permission_deve_retornar_false_se_inscricao_nao_estiver_em_mailbox_homologador(
            self
    ):
        mailbox_homologador = recipes.mailbox_homologador_inscricao.make(
            homologador=self.usuario_homologador
        )
        self.assertNotIn(self.inscricao, mailbox_homologador.inscricoes.all())
        self.assertFalse(self.view.has_permission())

    def test_has_permission_deve_retornar_false_se_avaliador_já_tiver_avaliado_a_mesma_inscricao(
            self
    ):
        mailbox_homologador = recipes.mailbox_homologador_inscricao.make(
            homologador=self.usuario_homologador
        )
        mailbox_homologador.inscricoes.add(self.inscricao)
        recipes.avaliacao_homologador.make(
            inscricao=self.inscricao, homologador=self.usuario_homologador
        )
        self.assertFalse(self.view.has_permission())

    @mock.patch("psct.models.analise.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    def test_has_permission_deve_retornar_false_se_fase_analise_nao_estiver_vigente(
            self, acontecendo
    ):
        acontecendo.return_value = False
        mailbox_homologador = recipes.mailbox_homologador_inscricao.make(
            homologador=self.usuario_homologador
        )
        mailbox_homologador.inscricoes.add(self.inscricao)
        self.assertFalse(self.view.has_permission())

    @mock.patch("psct.models.analise.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    def test_has_permission_deve_retornar_true_se_inscricao_nao_avaliada_esta_na_box_e_fase_vigente(
            self, acontecendo
    ):
        acontecendo.return_value = True
        mailbox_homologador = recipes.mailbox_homologador_inscricao.make(
            homologador=self.usuario_homologador
        )
        mailbox_homologador.inscricoes.add(self.inscricao)
        self.assertTrue(self.view.has_permission())

    def test_form_kwargs_deve_conter_inscricao(self):
        kwargs = self.view.get_form_kwargs()
        self.assertIn("inscricao", kwargs)
        self.assertEqual(self.inscricao, kwargs["inscricao"])

    def test_get_context_data_deve_conter_o_titulo_da_pagina(self):
        context = self.view.get_context_data()
        self.assertEqual(f"Avaliação da {self.inscricao_original}", context["titulo"])

    def test_get_context_data_deve_conter_inscricao_pre_analise(self):
        context = self.view.get_context_data()
        self.assertIn("inscricao", context)
        self.assertEqual(self.inscricao, context["inscricao"])

    def test_get_context_data_deve_conter_inscricao_original(self):
        context = self.view.get_context_data()
        self.assertIn("inscricao_original", context)
        self.assertEqual(self.inscricao_original, context["inscricao_original"])

    def test_get_context_data_deve_conter_o_breadcrumb_da_pagina(self):
        context = self.view.get_context_data()
        self.assertIn("breadcrumb", context)
        self.assertIn(("Inscrições", reverse("list_inscricao_psct")), context["breadcrumb"])
        self.assertIn(("Avaliar inscrição", ""), context["breadcrumb"])


class UpdateAvaliacaoHomologadorInscricaoViewTestCase(
    mixins.HomologadorPSCTTestData,
    mixins.InscricaoPreAnaliseTestData,
    mixins.EditalTestData,
    mixins.CursoTestData,
    TestCase
):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.avaliacao = recipes.avaliacao_homologador.make(inscricao=cls.inscricao)
        cls.view_url = reverse(
            "change_avaliacao_homologador_inscricao_psct", args=[cls.avaliacao.id]
        )
        cls.request = RequestFactory().get(cls.view_url)
        cls.request.user = cls.usuario_homologador
        cls.view = views.UpdateAvaliacaoHomologadorInscricaoView()
        cls.view.setup(cls.request, pk=cls.avaliacao.id)
        cls.view.object = None

    def test_has_permission_deve_retornar_false_se_usuario_nao_estah_no_grupo_homologador(self):
        request = RequestFactory().get(self.view_url)
        request.user = base.tests.recipes.user.make()
        view = views.UpdateAvaliacaoHomologadorInscricaoView()
        view.setup(request, pk=self.avaliacao.id)
        self.assertFalse(self.view.has_permission())

    def test_has_permission_deve_lancar_permission_denied_se_avaliacao_nao_existir(self):
        view = views.UpdateAvaliacaoHomologadorInscricaoView()
        view.setup(self.request, pk=0)
        with self.assertRaises(PermissionDenied):
            view.has_permission()

    @mock.patch("psct.models.analise.AvaliacaoHomologador.pode_alterar")
    def test_has_permission_deve_retornar_false_se_homologador_nao_pode_alterar_avaliacao(
            self, pode_alterar
    ):
        pode_alterar.return_value = False
        self.assertFalse(self.view.has_permission())

    @mock.patch("psct.models.analise.AvaliacaoHomologador.pode_alterar")
    def test_has_permission_deve_retornar_true_se_homologador_pode_alterar_avaliacao(
            self, pode_alterar
    ):
        pode_alterar.return_value = True
        self.assertTrue(self.view.has_permission())

    def test_form_kwargs_deve_conter_inscricao(self):
        kwargs = self.view.get_form_kwargs()
        self.assertIn("inscricao", kwargs)
        self.assertEqual(self.inscricao, kwargs["inscricao"])

    def test_get_context_data_deve_conter_o_titulo_da_pagina(self):
        context = self.view.get_context_data()
        self.assertEqual(f"Avaliação da {self.inscricao_original}", context["titulo"])

    def test_get_context_data_deve_conter_inscricao_pre_analise(self):
        context = self.view.get_context_data()
        self.assertIn("inscricao", context)
        self.assertEqual(self.inscricao, context["inscricao"])

    def test_get_context_data_deve_conter_inscricao_original(self):
        context = self.view.get_context_data()
        self.assertIn("inscricao_original", context)
        self.assertEqual(self.inscricao_original, context["inscricao_original"])

    def test_get_context_data_deve_conter_o_breadcrumb_da_pagina(self):
        context = self.view.get_context_data()
        self.assertIn("breadcrumb", context)
        self.assertIn(("Inscrições", reverse("list_inscricao_psct")), context["breadcrumb"])
        self.assertIn(("Avaliar inscrição", ""), context["breadcrumb"])

    def test_form_invalid_deve_adicionar_mensagem_de_erro(self):
        request = RequestFactory().get(self.view_url)
        request.user = self.usuario_homologador
        request.session = {}
        storage = default_storage(request)
        request._messages = storage
        view = views.UpdateAvaliacaoHomologadorInscricaoView()
        view.setup(request, pk=self.avaliacao.id)
        view.object = None
        view.form_invalid(mock.Mock())
        self.assertTrue(storage.added_new)
        self.assertIn(
            "Por favor, corrija os erros abaixo para continuar.", [m.message for m in storage]
        )


class AvaliacaoHomologadorViewTestCase(
    mixins.HomologadorPSCTTestData,
    mixins.InscricaoPreAnaliseTestData,
    mixins.EditalTestData,
    mixins.CursoTestData,
    TestCase
):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.avaliacao = recipes.avaliacao_homologador.make(inscricao=cls.inscricao)
        cls.view_url = reverse("view_avaliacao_homologador_inscricao_psct", args=[cls.avaliacao.id])
        cls.request = RequestFactory().get(cls.view_url)
        cls.request.user = cls.usuario_homologador
        cls.view = views.AvaliacaoHomologadorView()
        cls.view.setup(cls.request, pk=cls.avaliacao.id)
        cls.view.object = None

    def test_has_permission_deve_retornar_false_se_usuario_nao_estah_no_grupo_homologador(self):
        request = RequestFactory().get(self.view_url)
        request.user = base.tests.recipes.user.make()
        view = views.AvaliacaoHomologadorView()
        view.setup(request, pk=self.avaliacao.id)
        self.assertFalse(self.view.has_permission())

    def test_has_permission_deve_lancar_permission_denied_se_avaliacao_nao_existir(self):
        view = views.AvaliacaoHomologadorView()
        view.setup(self.request, pk=0)
        with self.assertRaises(PermissionDenied):
            view.has_permission()

    @mock.patch("psct.models.analise.AvaliacaoHomologador.is_owner")
    def test_has_permission_deve_retornar_false_se_avaliador_nao_eh_dono_da_avaliacao(
            self, is_owner
    ):
        is_owner.return_value = False
        self.assertFalse(self.view.has_permission())

    @mock.patch("psct.models.analise.AvaliacaoHomologador.is_owner")
    def test_has_permission_deve_retornar_true_se_avaliador_eh_dono_da_avaliacao(
            self, is_owner
    ):
        is_owner.return_value = True
        self.assertTrue(self.view.has_permission())

    def test_get_context_data_deve_conter_o_titulo_da_pagina(self):
        context = self.view.get_context_data()
        self.assertEqual(f"Avaliação da {self.inscricao_original}", context["titulo"])

    def test_get_context_data_deve_conter_inscricao_pre_analise(self):
        context = self.view.get_context_data()
        self.assertIn("inscricao", context)
        self.assertEqual(self.inscricao, context["inscricao"])

    def test_get_context_data_deve_conter_inscricao_original(self):
        context = self.view.get_context_data()
        self.assertIn("inscricao_original", context)
        self.assertEqual(self.inscricao_original, context["inscricao_original"])

    def test_get_context_data_deve_conter_o_breadcrumb_da_pagina(self):
        context = self.view.get_context_data()
        self.assertIn("breadcrumb", context)
        self.assertIn(("Inscrições", reverse("list_inscricao_psct")), context["breadcrumb"])
        self.assertIn((f"Avaliação #{self.avaliacao.id}", ""), context["breadcrumb"])
