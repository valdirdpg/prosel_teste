from django.shortcuts import reverse
from django.test import TestCase, RequestFactory

from cursos.tests.mixins import DiretorEnsinoPermissionData
from .. import recipes
from ..mixins import AdministradorPSCTTestData
from ...views import consulta as views


class DashboardViewTestCase(DiretorEnsinoPermissionData, AdministradorPSCTTestData, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.request = RequestFactory().get(reverse("base"))
        cls.request.user = cls.usuario_administrador
        cls.view = views.DashboardView()
        cls.view.setup(cls.request)
        cls.view.object = None

    def test_get_context_data_deveria_retornar_campi_com_processo_inscricao(self):
        curso_edital = recipes.curso_edital.make()
        recipes.processo_inscricao.make(edital=curso_edital.edital, cursos=[curso_edital.curso])
        context = self.view.get_context_data()
        self.assertIn(curso_edital.curso.campus, context['campi'])

    def test_get_context_data_nao_deveria_retornar_campi_com_processo_inscricao(self):
        recipes.curso_edital.make()
        context = self.view.get_context_data()
        self.assertFalse(context['campi'].exists())
