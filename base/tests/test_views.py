from django.test import RequestFactory, TestCase
from django.urls import reverse

from model_mommy import mommy

import candidatos.permissions
import psct.permissions
import noticias.tests.recipes
import editais.tests.recipes
import cursos.permissions
from . import recipes
from .. import views


class BaseViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        psct.permissions.CandidatosPSCT().sync()
        candidatos.permissions.Candidatos().sync()

    def setUp(self):
        super().setUp()
        request_factory = RequestFactory()
        self.request = request_factory.get(reverse("processoseletivo"))
        self.request.user = recipes.user.make()
        self.view = views.BaseView()
        self.view.setup(self.request)

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.get_template_names(), ["processoseletivo/index2.html"])

    def test_template_deveria_ser_diferente_para_candidatos(self):
        candidatos.permissions.Candidatos.add_user(self.request.user)
        self.assertEqual(self.view.get_template_names(), ["base/index_candidato.html"])

    def test_template_deveria_ser_diferente_para_candidatos_do_psct(self):
        psct.permissions.CandidatosPSCT.add_user(self.request.user)
        self.assertEqual(self.view.get_template_names(), ["base/index_candidato.html"])

    def test_get_context_data_deveria_ter_noticias_em_destaque(self):
        noticia = noticias.tests.recipes.noticia.make(
            publicado=True,
            destaque=True,
        )
        context = self.view.get_context_data()
        self.assertIn("destaques", context)
        self.assertIn(noticia, context["destaques"])

    def test_get_context_data_deveria_ter_ultimas_noticias(self):
        context = self.view.get_context_data()
        self.assertIn("ultimas", context)

    def test_ultimas_noticias_deveria_excluir_as_que_sao_destaque(self):
        destaque = noticias.tests.recipes.noticia.make(
            publicado=True,
            destaque=True,
        )
        ultima = noticias.tests.recipes.noticia.make(
            publicado=True,
            destaque=False,
        )
        context = self.view.get_context_data()
        self.assertNotIn(destaque, context["ultimas"])
        self.assertIn(ultima, context["ultimas"])

    def test_get_context_data_deveria_ter_grupos_de_noticias(self):
        context = self.view.get_context_data()
        self.assertIn("grupos", context)

    def test_grupos_de_noticias_deveria_ter_assunto_da_pagina_inicial(self):
        assunto = noticias.tests.recipes.assunto.make(pagina_inicial=True)
        noticias.tests.recipes.noticia.make(assunto=assunto)
        context = self.view.get_context_data()
        self.assertIn(assunto, context["grupos"][0])


class SearchViewViewTestCase(TestCase):

    def setUp(self):
        super().setUp()
        request_factory = RequestFactory()
        self.request = request_factory.get(reverse("processoseletivo"))
        self.request.user = recipes.user.make()
        self.view = views.SearchView()
        self.view.setup(self.request)

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.get_template_names(), ["base/search.html"])

    def test_get_context_data_deveria_retornar_parametro_buscado(self):
        self.request.GET = {"q": "teste"}
        self.view.setup(self.request)
        context = self.view.get_context_data()
        self.assertEqual("teste", context["q"])

    def test_get_context_data_deveria_retornar_noticia_na_busca(self):
        noticia = noticias.tests.recipes.noticia.make()
        self.request.GET = {"q": noticia.titulo}
        self.view.setup(self.request)
        context = self.view.get_context_data()
        self.assertIn(noticia, context["resultados"])

    def test_get_context_data_deveria_retornar_edital_na_busca(self):
        edital = editais.tests.recipes.edital.make()
        self.request.GET = {"q": edital.nome}
        self.view.setup(self.request)
        context = self.view.get_context_data()
        self.assertIn(edital, context["resultados"])

    def test_get_context_data_deveria_retornar_processo_seletivo_na_busca(self):
        processo_seletivo = mommy.make("processoseletivo.ProcessoSeletivo")
        self.request.GET = {"q": processo_seletivo.nome}
        self.view.setup(self.request)
        context = self.view.get_context_data()
        self.assertIn(processo_seletivo, context["resultados"])

    def test_get_context_data_deveria_retornar_curso_na_busca(self):
        cursos.permissions.DiretoresdeEnsino().sync()
        curso = mommy.make("cursos.CursoNoCampus")
        self.request.GET = {"q": curso.nome}
        self.view.setup(self.request)
        context = self.view.get_context_data()
        self.assertIn(curso, context["resultados"])

    def test_get_context_data_deveria_retornar_paginado_para_mais_de_5_itens(self):
        mommy.make("processoseletivo.ProcessoSeletivo", nome="a", _quantity=6)
        self.request.GET = {"q": "a"}
        self.view.setup(self.request)
        context = self.view.get_context_data()
        self.assertIn("paginado", context)
