from unittest import expectedFailure
from unittest import mock

from django.contrib.messages.storage import default_storage
from django.forms import Form
from django.http import Http404
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse_lazy

import cursos.recipes
from cursos.models import Campus
from psct import forms
from psct import models
from psct import permissions
from psct.tests import recipes
from psct.views import resultado as views


class ResultadoPreliminarViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.fase_analise_patcher = mock.patch.object(
            models.FaseAnalise,
            "atualizar_grupos_permissao",
        )
        cls.fase_analise_patcher.start()
        cls.processo_inscricao = recipes.processo_inscricao.make()
        cls.fase_analise = recipes.fase_analise.make(edital=cls.processo_inscricao.edital)

    def setUp(self) -> None:
        super().setUp()
        self.view = views.ResultadoPreliminarView()
        request = mock.Mock()
        self.view.setup(request, fase_pk=self.fase_analise.id)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.fase_analise_patcher.stop()

    def test_group_required_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            permissions.AdministradoresPSCT.name,
            views.ResultadoPreliminarView.group_required
        )

    def test_raise_exception_deveria_ser_true(self):
        self.assertTrue(views.ResultadoPreliminarView.raise_exception)

    def test_template_name_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            "psct/base/confirmacao.html",
            views.ResultadoPreliminarView.template_name
        )

    def test_form_class_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            Form,
            views.ResultadoPreliminarView.form_class
        )

    def test_setup_deve_definir_atributo_fase(self):
        self.assertTrue(hasattr(self.view, "fase"))

    def test_setup_deve_lancar_404_se_id_fase_nao_existe(self):
        view = views.ResultadoPreliminarView()
        request = mock.Mock()
        with self.assertRaises(Http404):
            view.setup(request, fase_pk=999)

    def test_get_context_data_deve_ter_back_url_igual_a_success_url(self):
        context = self.view.get_context_data()
        self.assertEqual(self.view.success_url, context["back_url"])

    @expectedFailure
    def test_get_context_data_deve_preencher_back_url_com_url_valida(self):
        context = self.view.get_context_data()
        self.assertIsNotNone(context["back_url"])

    def test_get_context_data_deve_ter_titulo(self):
        context = self.view.get_context_data()
        self.assertEqual(
            f"Deseja gerar o resultado preliminar do {self.fase_analise.edital}?",
            context["titulo"]
        )

    def test_get_context_data_deve_ter_nome_botao(self):
        context = self.view.get_context_data()
        self.assertEqual(
            "Confirmar",
            context["nome_botao"]
        )

    @mock.patch("psct.views.resultado.BreadCrumb.create")
    def test_get_context_data_deve_ter_breadcrumb(self, create):
        context = self.view.get_context_data()
        self.assertEqual(
            create.return_value,
            context["breadcrumb"]
        )

    @mock.patch("psct.views.resultado.generic.FormView.form_valid")
    @mock.patch("psct.views.resultado.tasks.gerar_resultado_preliminar.delay")
    @mock.patch("psct.views.resultado.Job")
    def test_form_valid_deve_gerar_resultado_preliminar(self, job, delay, form_valid):
        self.view.form_valid(form=mock.Mock())
        delay.assert_called_with(self.fase_analise.id)

    @mock.patch("psct.views.resultado.generic.FormView.form_valid")
    @mock.patch("psct.views.resultado.tasks.gerar_resultado_preliminar")
    @mock.patch("psct.views.resultado.Job.new")
    def test_form_valid_deve_criar_job(self, new, gerar_resultado_preliminar, form_valid):
        gerar_resultado_preliminar.name = "name"
        self.view.form_valid(form=mock.Mock())
        new.assert_called_with(
            self.view.request.user,
            gerar_resultado_preliminar.delay.return_value,
            name=gerar_resultado_preliminar.name
        )

    @mock.patch("psct.views.resultado.generic.FormView.form_valid")
    @mock.patch("psct.views.resultado.tasks.gerar_resultado_preliminar")
    @mock.patch("psct.views.resultado.Job.new")
    def test_form_valid_deve_adicionar_mensagem_de_sucesso(
            self, new, gerar_resultado_preliminar, form_valid
    ):
        request = RequestFactory().get("/")
        request.user = mock.Mock()
        request.session = {}
        view = views.ResultadoPreliminarView()
        view.setup(request, fase_pk=self.fase_analise.id)
        storage = default_storage(request)
        request._messages = storage
        view.form_valid(form=mock.Mock())
        self.assertTrue(storage.added_new)
        self.assertIn(
            "Sua solicitação está sendo processada."
            " Esta operação pode demorar alguns minutos.",
            [m.message for m in storage]
        )

    def test_get_success_url_deveria_pegar_valor_a_partir_do_job(self):
        self.view.job = mock.Mock()
        self.assertEqual(
            self.view.job.get_absolute_url.return_value,
            self.view.get_success_url()
        )


class ResultadoFileViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.fase_analise_patcher = mock.patch.object(
            models.FaseAnalise,
            "atualizar_grupos_permissao",
        )
        cls.fase_analise_patcher.start()
        cls.resultado = recipes.resultado_preliminar.make()

    def setUp(self) -> None:
        super().setUp()
        self.view = views.ResultadoFileView()
        request = mock.Mock()
        self.view.setup(request, resultado_pk=self.resultado.id)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.fase_analise_patcher.stop()

    def test_group_required_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            permissions.AdministradoresPSCT.name,
            views.ResultadoFileView.group_required
        )

    def test_raise_exception_deveria_ser_true(self):
        self.assertTrue(views.ResultadoFileView.raise_exception)

    def test_template_name_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            "psct/base/confirmacao.html",
            views.ResultadoFileView.template_name
        )

    def test_form_class_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            forms.FileFormatForm,
            views.ResultadoFileView.form_class
        )

    def test_success_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            reverse_lazy("admin:psct_resultadopreliminar_changelist"),
            views.ResultadoFileView.success_url
        )

    def test_setup_deve_definir_atributo_resultado(self):
        self.assertTrue(hasattr(self.view, "resultado"))

    def test_setup_deve_lancar_404_se_id_resultado_nao_existe(self):
        view = views.ResultadoFileView()
        request = mock.Mock()
        with self.assertRaises(Http404):
            view.setup(request, resultado_pk=999)

    def test_get_context_data_deve_ter_back_url_igual_a_success_url(self):
        context = self.view.get_context_data()
        self.assertEqual(self.view.success_url, context["back_url"])

    def test_get_context_data_deve_ter_titulo(self):
        context = self.view.get_context_data()
        self.assertEqual(
            f"Deseja exportar para arquivo o resultado do {self.resultado.fase.edital}?",
            context["titulo"]
        )

    def test_get_context_data_deve_ter_nome_botao(self):
        context = self.view.get_context_data()
        self.assertEqual(
            "Confirmar",
            context["nome_botao"]
        )

    @mock.patch("psct.views.resultado.BreadCrumb.create")
    def test_get_context_data_deve_ter_breadcrumb(self, create):
        context = self.view.get_context_data()
        self.assertEqual(
            create.return_value,
            context["breadcrumb"]
        )

    @mock.patch("psct.views.resultado.tasks.exportar_resultado_arquivo.delay")
    def test_form_valid_deve_exportar_resultado_arquivo(self, delay):
        render = mock.Mock()
        filetype = mock.Mock()
        form = mock.Mock()
        form.cleaned_data = {
            "render": render,
            "filetype": filetype,
        }
        self.view.form_valid(form)
        delay.assert_called_with(
            self.view.request.user.id, self.resultado.id, render, filetype
        )

    @mock.patch("psct.views.resultado.tasks.exportar_resultado_arquivo.delay")
    @mock.patch("psct.views.resultado.generic.FormView.form_valid")
    def test_form_valid_deve_adicionar_mensagem_de_sucesso(self, form_valid, delay):
        request = RequestFactory().get("/")
        request.user = mock.Mock()
        request.session = {}
        view = views.ResultadoFileView()
        view.setup(request, resultado_pk=self.resultado.id)
        storage = default_storage(request)
        request._messages = storage
        view.form_valid(form=mock.MagicMock())
        self.assertTrue(storage.added_new)
        self.assertIn(
            "Sua solicitação está sendo processada. Você receberá os arquivos por e-mail.",
            [m.message for m in storage]
        )


class GenericCreateResultadoViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.fase_analise_patcher = mock.patch.object(
            models.FaseAnalise,
            "atualizar_grupos_permissao",
        )
        cls.fase_analise_patcher.start()
        cls.resultado = recipes.resultado_preliminar.make()

    def setUp(self) -> None:
        super().setUp()
        self.view = views.GenericCreateResultadoView()
        request = mock.Mock()
        self.view.setup(request, pk=self.resultado.id)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.fase_analise_patcher.stop()

    def test_group_required_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            permissions.AdministradoresPSCT.name,
            views.GenericCreateResultadoView.group_required
        )

    def test_raise_exception_deveria_ser_true(self):
        self.assertTrue(views.GenericCreateResultadoView.raise_exception)

    def test_template_name_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            "psct/base/confirmacao.html",
            views.GenericCreateResultadoView.template_name
        )

    def test_form_class_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            Form,
            views.GenericCreateResultadoView.form_class
        )

    def test_success_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            reverse_lazy("admin:psct_resultadopreliminar_changelist"),
            views.GenericCreateResultadoView.success_url
        )

    def test_setup_deve_definir_atributo_resultado(self):
        self.assertTrue(hasattr(self.view, "resultado"))

    def test_setup_deve_lancar_404_se_id_resultado_nao_existe(self):
        view = views.GenericCreateResultadoView()
        request = mock.Mock()
        with self.assertRaises(Http404):
            view.setup(request, pk=999)

    def test_get_title_deveria_ser_vazio(self):
        self.assertEqual("", self.view.get_title())

    def test_get_extra_message_deveria_ser_vazio(self):
        self.assertEqual("", self.view.get_extra_message())

    def test_get_context_data_deve_ter_back_url_igual_a_success_url(self):
        context = self.view.get_context_data()
        self.assertEqual(self.view.success_url, context["back_url"])

    def test_get_context_data_deve_ter_titulo(self):
        context = self.view.get_context_data()
        self.assertEqual(
            self.view.get_title(),
            context["titulo"]
        )

    def test_get_context_data_deve_ter_nome_botao(self):
        context = self.view.get_context_data()
        self.assertEqual(
            "Confirmar",
            context["nome_botao"]
        )

    @mock.patch("psct.views.resultado.BreadCrumb.create")
    def test_get_context_data_deve_ter_breadcrumb(self, create):
        context = self.view.get_context_data()
        self.assertEqual(
            create.return_value,
            context["breadcrumb"]
        )

    def test_get_context_data_deve_ter_extra_message(self):
        context = self.view.get_context_data()
        self.assertEqual(
            self.view.get_extra_message(),
            context["extra_message"]
        )

    def test_form_valid_deve_criar_objeto_a_partir_do_model(self):
        self.view.model = mock.Mock()
        form = mock.Mock()
        self.view.form_valid(form)
        self.view.model.objects.create.assert_called_with(
            resultado=self.resultado, edital=self.resultado.fase.edital
        )

    @mock.patch("psct.views.resultado.generic.FormView.form_valid")
    def test_form_valid_deve_adicionar_mensagem_de_sucesso(self, form_valid):
        request = RequestFactory().get("/")
        request.user = mock.Mock()
        request.session = {}
        view = views.GenericCreateResultadoView()
        view.setup(request, pk=self.resultado.id)
        view.model = mock.Mock()
        view.success_message = "Teste"
        storage = default_storage(request)
        request._messages = storage
        view.form_valid(form=mock.MagicMock())
        self.assertTrue(storage.added_new)
        self.assertIn(
            view.success_message,
            [m.message for m in storage]
        )

    @mock.patch("psct.views.resultado.GroupRequiredMixin.has_permission")
    def test_has_permission_deve_ser_verdadeiro_se_edital_tem_reverse_field_name(
            self, has_permission
    ):
        has_permission.return_value = True
        self.view.reverse_field_name = "teste_field_name"
        self.view.resultado.fase.edital.teste_field_name = "any value"
        self.assertTrue(
            self.view.has_permission()
        )

    def test_has_permission_deve_ser_falso_se_edital_nao_tem_reverse_field_name(self):
        self.view.reverse_field_name = ""
        self.assertFalse(
            self.view.has_permission()
        )


class GenericDeleteResultadoViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.fase_analise_patcher = mock.patch.object(
            models.FaseAnalise,
            "atualizar_grupos_permissao",
        )
        cls.fase_analise_patcher.start()
        cls.resultado = recipes.resultado_preliminar.make()

    def setUp(self) -> None:
        super().setUp()
        self.view = views.GenericDeleteResultadoView()
        request = mock.Mock()
        self.view.setup(request, pk=self.resultado.id)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.fase_analise_patcher.stop()

    def test_group_required_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            permissions.AdministradoresPSCT.name,
            views.GenericDeleteResultadoView.group_required
        )

    def test_raise_exception_deveria_ser_true(self):
        self.assertTrue(views.GenericDeleteResultadoView.raise_exception)

    def test_template_name_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            "psct/base/confirmacao.html",
            views.GenericDeleteResultadoView.template_name
        )

    def test_form_class_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            Form,
            views.GenericDeleteResultadoView.form_class
        )

    def test_success_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            reverse_lazy("admin:psct_resultadopreliminar_changelist"),
            views.GenericDeleteResultadoView.success_url
        )

    def test_setup_deve_definir_atributo_resultado(self):
        self.assertTrue(hasattr(self.view, "resultado"))

    def test_setup_deve_lancar_404_se_id_resultado_nao_existe(self):
        view = views.GenericDeleteResultadoView()
        request = mock.Mock()
        with self.assertRaises(Http404):
            view.setup(request, pk=999)

    def test_get_title_deveria_ser_vazio(self):
        self.assertEqual("", self.view.get_title())

    def test_get_extra_message_deveria_ser_vazio(self):
        self.assertEqual("", self.view.get_extra_message())

    def test_get_context_data_deve_ter_back_url_igual_a_success_url(self):
        context = self.view.get_context_data()
        self.assertEqual(self.view.success_url, context["back_url"])

    def test_get_context_data_deve_ter_titulo(self):
        context = self.view.get_context_data()
        self.assertEqual(
            self.view.get_title(),
            context["titulo"]
        )

    def test_get_context_data_deve_ter_nome_botao(self):
        context = self.view.get_context_data()
        self.assertEqual(
            "Confirmar",
            context["nome_botao"]
        )

    @mock.patch("psct.views.resultado.BreadCrumb.create")
    def test_get_context_data_deve_ter_breadcrumb(self, create):
        context = self.view.get_context_data()
        self.assertEqual(
            create.return_value,
            context["breadcrumb"]
        )

    def test_get_context_data_deve_ter_extra_message(self):
        context = self.view.get_context_data()
        self.assertEqual(
            self.view.get_extra_message(),
            context["extra_message"]
        )

    @mock.patch("psct.views.resultado.generic.FormView.form_valid")
    def test_form_valid_deve_excluir_objeto_a_partir_do_model(self, form_valid):
        self.view.model = mock.Mock()
        form = mock.Mock()
        self.view.form_valid(form)
        self.view.model.objects.filter.assert_called_with(
            resultado=self.resultado, edital=self.resultado.fase.edital
        )
        self.view.model.objects.filter.return_value.delete.assert_called_once()

    @mock.patch("psct.views.resultado.generic.FormView.form_valid")
    def test_form_valid_deve_adicionar_mensagem_de_sucesso(self, form_valid):
        request = RequestFactory().get("/")
        request.user = mock.Mock()
        request.session = {}
        view = views.GenericDeleteResultadoView()
        view.setup(request, pk=self.resultado.id)
        view.model = mock.Mock()
        view.success_message = "Teste"
        storage = default_storage(request)
        request._messages = storage
        view.form_valid(form=mock.MagicMock())
        self.assertTrue(storage.added_new)
        self.assertIn(
            view.success_message,
            [m.message for m in storage]
        )

    @mock.patch("psct.views.resultado.GroupRequiredMixin.has_permission")
    def test_has_permission_deve_ser_verdadeiro_se_edital_tem_reverse_field_name(
            self, has_permission
    ):
        has_permission.return_value = True
        self.view.reverse_field_name = "teste_field_name"
        self.view.resultado.fase.edital.teste_field_name = "any value"
        self.assertTrue(
            self.view.has_permission()
        )

    def test_has_permission_deve_ser_falso_se_edital_nao_tem_reverse_field_name(self):
        self.view.reverse_field_name = ""
        self.assertFalse(
            self.view.has_permission()
        )


class HomologarResultadoPreliminarViewTestCase(TestCase):

    def test_reverse_field_name_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            "resultado_preliminar",
            views.HomologarResultadoPreliminarView.reverse_field_name
        )

    def test_model_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            models.ResultadoPreliminarHomologado,
            views.HomologarResultadoPreliminarView.model
        )

    def test_breadcrumb_title_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            "Definir resultado preliminar",
            views.HomologarResultadoPreliminarView.breadcrumb_title
        )

    def test_success_message_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            "Resultado preliminar definido com sucesso.",
            views.HomologarResultadoPreliminarView.success_message
        )

    def test_get_title_deve_esta_corretamente_configurado(self):
        view = views.HomologarResultadoPreliminarView()
        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            view.resultado = recipes.resultado_preliminar.make()
        self.assertEqual(
            f"Definir resultado preliminar do {view.resultado.fase.edital}",
            view.get_title()
        )

    def test_get_extra_message_deve_esta_corretamente_configurado(self):
        view = views.HomologarResultadoPreliminarView()
        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            view.resultado = recipes.resultado_preliminar.make()
        self.assertEqual(
            f"Deseja realmente definir o {view.resultado} oficialmente como "
            f"resultado preliminar do {view.resultado.fase.edital}?",
            view.get_extra_message()
        )


class RemoverHomologacaoResultadoPreliminarViewTestCase(TestCase):

    def test_reverse_field_name_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            "resultado_preliminar",
            views.RemoverHomologacaoResultadoPreliminarView.reverse_field_name
        )

    def test_model_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            models.ResultadoPreliminarHomologado,
            views.RemoverHomologacaoResultadoPreliminarView.model
        )

    def test_breadcrumb_title_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            "Remover resultado preliminar",
            views.RemoverHomologacaoResultadoPreliminarView.breadcrumb_title
        )

    def test_success_message_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            "Resultado preliminar removido com sucesso.",
            views.RemoverHomologacaoResultadoPreliminarView.success_message
        )

    def test_get_title_deve_esta_corretamente_configurado(self):
        view = views.RemoverHomologacaoResultadoPreliminarView()
        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            view.resultado = recipes.resultado_preliminar.make()
        self.assertEqual(
            f"Remover a homologação do resultado preliminar do {view.resultado.fase.edital}",
            view.get_title()
        )

    def test_get_extra_message_deve_esta_corretamente_configurado(self):
        view = views.RemoverHomologacaoResultadoPreliminarView()
        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            view.resultado = recipes.resultado_preliminar.make()
        self.assertEqual(
            f"Deseja realmente remover o resultado preliminar do {view.resultado.fase.edital}?",
            view.get_extra_message()
        )


class DeleteResultadoViewTestCase(TestCase):

    def test_reverse_field_name_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            "resultado",
            views.DeleteResultadoView.reverse_field_name
        )

    def test_model_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            models.ResultadoFinal,
            views.DeleteResultadoView.model
        )

    def test_breadcrumb_title_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            "Remover resultado",
            views.DeleteResultadoView.breadcrumb_title
        )

    def test_success_message_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            "Resultado removido com sucesso.",
            views.DeleteResultadoView.success_message
        )

    def test_get_title_deve_esta_corretamente_configurado(self):
        view = views.DeleteResultadoView()
        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            view.resultado = recipes.resultado_preliminar.make()
        self.assertEqual(
            f"Remover o resultado do {view.resultado.fase.edital}",
            view.get_title()
        )

    def test_get_extra_message_deve_esta_corretamente_configurado(self):
        view = views.DeleteResultadoView()
        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            view.resultado = recipes.resultado_preliminar.make()
        self.assertEqual(
            f"Deseja realmente remover o resultado do {view.resultado.fase.edital}?",
            view.get_extra_message()
        )


class CreateResultadoViewTestCase(TestCase):

    def test_reverse_field_name_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            "resultado",
            views.CreateResultadoView.reverse_field_name
        )

    def test_model_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            models.ResultadoFinal,
            views.CreateResultadoView.model
        )

    def test_breadcrumb_title_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            "Definir resultado",
            views.CreateResultadoView.breadcrumb_title
        )

    def test_success_message_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            "Resultado definido com sucesso.",
            views.CreateResultadoView.success_message
        )

    def test_get_title_deve_esta_corretamente_configurado(self):
        view = views.CreateResultadoView()
        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            view.resultado = recipes.resultado_preliminar.make()
        self.assertEqual(
            f"Definir resultado do {view.resultado.fase.edital}",
            view.get_title()
        )

    def test_get_extra_message_deve_esta_corretamente_configurado(self):
        view = views.CreateResultadoView()
        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            view.resultado = recipes.resultado_preliminar.make()
        self.assertEqual(
            f"Deseja realmente definir o {view.resultado} oficialmente "
            f"como resultado do {view.resultado.fase.edital}?",
            view.get_extra_message()
        )


class ResultadoInscricaoViewTestCase(TestCase):
    def test_group_required_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            permissions.CandidatosPSCT.name,
            views.ResultadoInscricaoView.group_required
        )

    def test_raise_exception_deveria_ser_true(self):
        self.assertTrue(views.ResultadoInscricaoView.raise_exception)

    def test_template_name_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            "psct/resultado/extrato.html",
            views.ResultadoInscricaoView.template_name
        )

    @mock.patch("psct.views.resultado.get_object_or_404")
    def test_setup_deveria_criar_atributo_inscricao_a_partir_do_pk(self, get_object_or_404):
        view = views.ResultadoInscricaoView()
        request = mock.Mock()
        view.setup(request, pk=1)
        self.assertEqual(get_object_or_404.return_value, view.inscricao)

    def test_setup_deve_lancar_404_se_id_resultado_nao_existe(self):
        view = views.ResultadoInscricaoView()
        request = mock.Mock()
        with self.assertRaises(Http404):
            view.setup(request, pk=999)

    @mock.patch("psct.views.resultado.GroupRequiredMixin.has_permission")
    def test_has_permission_deve_ser_verdadeiro_se_candidato_pode_ver_resultado_preliminar(
            self, has_permission
    ):
        view = views.ResultadoInscricaoView()
        view.request = mock.Mock()
        view.inscricao = mock.Mock()
        has_permission.return_value = True
        view.inscricao.pode_ver_resultado_preliminar = True
        view.inscricao.is_owner.return_value = True
        self.assertTrue(view.has_permission())

    @mock.patch("psct.views.resultado.GroupRequiredMixin.has_permission")
    def test_has_permission_deve_ser_falso_se_nao_for_candidato_da_inscricao(
            self, has_permission
    ):
        view = views.ResultadoInscricaoView()
        view.request = mock.Mock()
        view.inscricao = mock.Mock()
        has_permission.return_value = True
        view.inscricao.pode_ver_resultado_preliminar = True
        view.inscricao.is_owner.return_value = False
        self.assertFalse(view.has_permission())

    @mock.patch("psct.views.resultado.GroupRequiredMixin.has_permission")
    def test_has_permission_deve_ser_falso_se_nao_pode_ver_resultado_preliminar(
            self, has_permission
    ):
        view = views.ResultadoInscricaoView()
        view.request = mock.Mock()
        view.inscricao = mock.Mock()
        has_permission.return_value = True
        view.inscricao.pode_ver_resultado_preliminar = False
        view.inscricao.is_owner.return_value = True
        self.assertFalse(view.has_permission())

    @mock.patch("psct.views.resultado.GroupRequiredMixin.has_permission")
    def test_has_permission_deve_ser_falso_se_nao_tiver_grupo_permissao_candidato_psct(
            self, has_permission
    ):
        view = views.ResultadoInscricaoView()
        view.request = mock.Mock()
        view.inscricao = mock.Mock()
        has_permission.return_value = False
        view.inscricao.pode_ver_resultado_preliminar = True
        view.inscricao.is_owner.return_value = True
        self.assertFalse(view.has_permission())

    @mock.patch("psct.views.resultado.generic.TemplateView.get_context_data")
    def test_get_context_data_deve_ter_inscricao(self, get_context_data):
        get_context_data.return_value = {}
        view = views.ResultadoInscricaoView()
        view.inscricao = mock.Mock()
        self.assertEqual(view.inscricao, view.get_context_data()["inscricao"])

    @mock.patch("psct.views.resultado.generic.TemplateView.get_context_data")
    def test_get_context_data_deve_ter_resultado(self, get_context_data):
        get_context_data.return_value = {}
        view = views.ResultadoInscricaoView()
        view.inscricao = mock.Mock()
        self.assertEqual(
            view.inscricao.get_resultado.return_value,
            view.get_context_data()["resultado"]
        )

    @mock.patch("psct.views.resultado.generic.TemplateView.get_context_data")
    def test_get_context_data_deve_ter_situacao(self, get_context_data):
        get_context_data.return_value = {}
        view = views.ResultadoInscricaoView()
        view.inscricao = mock.Mock()
        self.assertEqual(
            view.inscricao.get_situacao.return_value,
            view.get_context_data()["situacao"]
        )

    @mock.patch("psct.views.resultado.generic.TemplateView.get_context_data")
    def test_get_context_data_deve_ter_pontuacao(self, get_context_data):
        get_context_data.return_value = {}
        view = views.ResultadoInscricaoView()
        view.inscricao = mock.Mock()
        self.assertEqual(
            view.inscricao.get_extrato_pontuacao.return_value,
            view.get_context_data()["pontuacao"]
        )

    @mock.patch("psct.views.resultado.generic.TemplateView.get_context_data")
    @mock.patch("psct.views.resultado.BreadCrumb.create")
    def test_get_context_data_deve_ter_breadcrumb(self, create, get_context_data):
        get_context_data.return_value = {}
        view = views.ResultadoInscricaoView()
        view.inscricao = mock.Mock()
        self.assertEqual(
            create.return_value,
            view.get_context_data()["breadcrumb"]
        )


class RodizioVagasViewTestCase(TestCase):
    def test_group_required_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            permissions.AdministradoresPSCT.name,
            views.RodizioVagasView.group_required
        )

    def test_raise_exception_deveria_ser_true(self):
        self.assertTrue(views.RodizioVagasView.raise_exception)

    def test_template_name_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            "psct/resultado/vagas.html",
            views.RodizioVagasView.template_name
        )

    def test_success_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            reverse_lazy("admin:psct_resultadopreliminar_changelist"),
            views.RodizioVagasView.success_url
        )

    @mock.patch("psct.views.resultado.generic.TemplateView.get_context_data")
    def test_get_context_data_deve_lancar_404_se_id_resultado_nao_existe(self, get_context_data):
        get_context_data.return_value = {}
        view = views.RodizioVagasView()
        view.kwargs = {"pk": 999}
        with self.assertRaises(Http404):
            view.get_context_data()

    @mock.patch("psct.views.resultado.generic.TemplateView.get_context_data")
    def test_get_context_data_deve_ter_resultado(self, get_context_data):
        get_context_data.return_value = {}
        view = views.RodizioVagasView()
        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            resultado = recipes.resultado_preliminar.make()
        request = mock.Mock()
        view.setup(request, pk=resultado.pk)
        self.assertEqual(
            resultado, view.get_context_data()["resultado"]
        )

    @mock.patch("psct.views.resultado.generic.TemplateView.get_context_data")
    @mock.patch("psct.views.resultado.BreadCrumb.create")
    def test_get_context_data_deve_ter_breadcrumb(self, create, get_context_data):
        get_context_data.return_value = {}
        view = views.RodizioVagasView()
        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            resultado = recipes.resultado_preliminar.make()
        request = mock.Mock()
        view.setup(request, pk=resultado.pk)
        self.assertEqual(
            create.return_value,
            view.get_context_data()["breadcrumb"]
        )

    @mock.patch("psct.views.resultado.generic.TemplateView.get_context_data")
    def test_get_context_data_deve_ter_campi(self, get_context_data):
        edital = recipes.edital.make()
        with mock.patch.multiple(
                Campus,
                cria_usuarios_diretores=mock.DEFAULT,
                adiciona_permissao_diretores=mock.DEFAULT,
                remove_permissao_diretores=mock.DEFAULT
        ):
            curso_selecao = cursos.recipes.curso_selecao.make()
            recipes.processo_inscricao.make(
                cursos=[curso_selecao],
                edital=edital,
            )

        with mock.patch.object(models.FaseAnalise, "atualizar_grupos_permissao"):
            resultado = recipes.resultado_preliminar.make(fase__edital=edital)
            vagas = recipes.vagas_resultado_preliminar.make(
                resultado_curso__resultado=resultado,
                resultado_curso__curso=curso_selecao,
            )

        curso_data = [[vagas.modalidade.resumo, vagas.quantidade]]
        campus_data = [[curso_selecao, curso_data]]
        campi = [[curso_selecao.campus, campus_data]]

        get_context_data.return_value = {}
        view = views.RodizioVagasView()
        request = mock.Mock()
        view.setup(request, pk=resultado.pk)
        self.assertEqual(campi, view.get_context_data()["campi"])
