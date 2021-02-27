from unittest import mock

from django.http import Http404
from django.test import RequestFactory, TestCase

import noticias.tests.recipes
import processoseletivo.recipes
from . import recipes
from .. import choices
from .. import views


class EditalViewTestCase(TestCase):
    def setUp(self):
        super().setUp()
        request_factory = RequestFactory()
        self.request = request_factory.get("/admin")
        self.request.user = mock.Mock()
        self.edital = recipes.edital.make()
        self.view = views.EditalView()
        self.view.setup(self.request, pk=self.edital)

    def test_get_context_data_deveria_ter_processos_passado_via_http_get(self):
        processo = processoseletivo.recipes.processo_seletivo.make()
        self.request.GET = {"processo": processo.id}
        self.view.setup(self.request, pk=self.edital.id)
        context = self.view.get_context_data()
        self.assertIn("processo", context)
        self.assertEqual(context["processo"], processo)

    def test_get_context_data_deveria_ter_editais_abertos(self):
        context = self.view.get_context_data()
        self.assertIn("editais_abertos", context)

    def test_editais_abertos_em_get_context_data_deveria_ter_edital(self):
        processo = processoseletivo.recipes.processo_seletivo.make()
        edital = recipes.edital.make(
            tipo=choices.EditalChoices.ABERTURA.name,
            edicao__processo_seletivo=processo,
            publicado=True,
            encerrado=False,
        )
        context = self.view.get_context_data()
        self.assertIn(edital, context["editais_abertos"])

    def test_get_context_data_deveria_ter_editais_abertos_paginados(self):
        processo = processoseletivo.recipes.processo_seletivo.make()
        recipes.edital.make(
            tipo=choices.EditalChoices.ABERTURA.name,
            edicao__processo_seletivo=processo,
            publicado=True,
            encerrado=False,
            _quantity=11,
        )
        context = self.view.get_context_data()
        self.assertIn("editais_abertos", context)
        self.assertIn("paginado", context)

    def test_get_context_data_deveria_ter_editais_abertos_por_pagina(self):
        processo = processoseletivo.recipes.processo_seletivo.make()
        recipes.edital.make(
            tipo=choices.EditalChoices.ABERTURA.name,
            edicao__processo_seletivo=processo,
            publicado=True,
            encerrado=False,
            _quantity=11,
        )
        request_factory = RequestFactory()
        request = request_factory.get("/admin")
        request.GET = {"page": "2"}
        self.view.setup(request, pk=self.edital.id)
        context = self.view.get_context_data()
        self.assertIn("editais_abertos", context)
        self.assertIn("paginado", context)

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.template_name, "editais/index.html")


class EditalArquivosViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.request.user = mock.Mock()
        cls.edital = recipes.edital.make()
        cls.view = views.EditalArquivosView()
        cls.categoria = choices.CategoriaDocumentoChoices.RESULTADO.name
        cls.view.setup(cls.request, pk_edital=cls.edital.id, categoria=cls.categoria)

    def test_get_context_data_deveria_ter_objeto_edital_do_id_passado_na_url(self):
        context = self.view.get_context_data()
        self.assertIn("edital", context)
        self.assertEqual(self.edital, context["edital"])

    def test_get_context_data_deveria_ter_label_da_categoria(self):
        context = self.view.get_context_data()
        label = choices.CategoriaDocumentoChoices.label(self.categoria)
        self.assertIn("categoria_label", context)
        self.assertEqual(label, context["categoria_label"])

    def test_get_context_data_deveria_ter_arquivos(self):
        context = self.view.get_context_data()
        self.assertIn("arquivos", context)

    def test_get_context_data_deveria_lancar_404_se_categoria_nao_existe(self):
        view = views.EditalArquivosView()
        view.setup(self.request, pk_edital=self.edital.id, categoria="NAO_EXISTE")
        with self.assertRaises(Http404):
            view.get_context_data()

    def test_get_context_data_deveria_filtrar_pela_categoria_prova(self):
        documento = recipes.documento.make(
            categoria=choices.CategoriaDocumentoChoices.PROVA.name
        )
        view = views.EditalArquivosView()
        view.setup(
            self.request,
            pk_edital=documento.edital.id,
            categoria=choices.CategoriaDocumentoChoices.PROVA.name,
        )
        context = view.get_context_data()
        self.assertIn(documento, context["arquivos"])

    def test_get_context_data_deveria_filtrar_pela_categoria_resultado(self):
        documento = recipes.documento.make(
            categoria=choices.CategoriaDocumentoChoices.RESULTADO.name
        )
        view = views.EditalArquivosView()
        view.setup(
            self.request,
            pk_edital=documento.edital.id,
            categoria=choices.CategoriaDocumentoChoices.RESULTADO.name,
        )
        context = view.get_context_data()
        self.assertIn(documento, context["arquivos"])

    def test_get_context_data_deveria_filtrar_por_qualquer_categoria(self):
        documento = recipes.documento.make(
            categoria=choices.CategoriaDocumentoChoices.EDITAL.name
        )
        view = views.EditalArquivosView()
        view.setup(
            self.request,
            pk_edital=documento.edital.id,
            categoria=choices.CategoriaDocumentoChoices.EDITAL.name,
        )
        context = view.get_context_data()
        self.assertIn(documento, context["arquivos"])

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.template_name, "editais/edital_arquivos.html")


class EditaisEncerradosViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.request.user = mock.Mock()
        cls.edital = recipes.edital.make()
        cls.view = views.EditaisEncerradosView()
        cls.view.setup(cls.request)

    def test_get_context_data_deveria_ter_processos_passado_via_http_get(self):
        request_factory = RequestFactory()
        self.request = request_factory.get("/admin")
        self.request.user = mock.Mock()
        processo = processoseletivo.recipes.processo_seletivo.make()
        self.request.GET = {"processo": processo.id}
        self.view = views.EditaisEncerradosView()
        self.view.setup(self.request, pk=self.edital.id)
        context = self.view.get_context_data()
        self.assertIn("processo", context)
        self.assertEqual(processo, context["processo"])

    def test_get_context_data_deveria_ter_editais_encerrados(self):
        processo = processoseletivo.recipes.processo_seletivo.make()
        edital = recipes.edital.make(
            tipo=choices.EditalChoices.ABERTURA.name,
            edicao__processo_seletivo=processo,
            publicado=True,
            encerrado=True,
        )
        context = self.view.get_context_data()
        self.assertIn("editais_encerrados", context)
        self.assertIn(edital, context["editais_encerrados"])

    def test_get_context_data_deveria_ter_editais_encerrados_paginados(self):
        processo = processoseletivo.recipes.processo_seletivo.make()
        recipes.edital.make(
            tipo=choices.EditalChoices.ABERTURA.name,
            edicao__processo_seletivo=processo,
            publicado=True,
            encerrado=True,
            _quantity=11,
        )
        context = self.view.get_context_data()
        self.assertIn("editais_encerrados", context)
        self.assertIn("paginado", context)
        self.assertEqual(10, len(context["editais_encerrados"]))

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.template_name, "editais/index.html")


class EditalDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.request.user = mock.Mock()
        cls.edital = recipes.edital.make()
        cls.view = views.EditalDetailView()
        cls.view.setup(cls.request, pk=cls.edital.id)

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.template_name, "editais/edital_detail.html")

    def test_get_context_data_deveria_ter_objeto_edital_do_id_passado_na_url(self):
        context = self.view.get_context_data()
        self.assertIn("edital", context)
        self.assertEqual(self.edital, context["edital"])

    def test_get_context_data_deveria_ter_noticias(self):
        noticia = noticias.tests.recipes.noticia.make(
            palavras_chave=[self.edital.palavra_chave]
        )
        context = self.view.get_context_data()
        self.assertIn("noticias", context)
        self.assertIn(noticia, context["noticias"])
