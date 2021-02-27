from unittest import mock

from django.test import override_settings, TestCase

from noticias.models import Assunto
from .. import configs
from .. import context_processors


class ConfigTestCase(TestCase):

    def test_deveria_ter_chave_config(self):
        self.assertIn("config", context_processors.config(mock.Mock()))

    def test_deveria_retornar_objeto_portal_config(self):
        self.assertEqual(configs.PortalConfig, context_processors.config(mock.Mock())["config"])

    def test_deveria_ter_chave_assuntos(self):
        self.assertIn("assuntos", context_processors.config(mock.Mock()))

    def test_deveria_retornar_objeto_assuntos(self):
        self.assertEqual(Assunto, context_processors.config(mock.Mock())["assuntos"].model)


class AppListTestCase(TestCase):

    @mock.patch("base.context_processors.admin.site.get_app_list")
    def test_deveria_ter_chave_apps_lista_de_apps_instaladas(self, get_app_list):
        get_app_list.return_value = ["app"]
        self.assertEqual(["app"], context_processors.apps_list(mock.Mock())["estudante_app_list"])

    @mock.patch("base.context_processors.admin.site.get_app_list")
    def test_deveria_ter_chave_apps_list(self, get_app_list):
        get_app_list.return_value = ["app"]
        self.assertIn("estudante_app_list", context_processors.apps_list(mock.Mock()))


@override_settings(DEBUG=True)
class DebugTestCase(TestCase):

    def test_obter_o_valor_a_partir_do_settings(self):
        self.assertTrue(context_processors.debug(mock.Mock()))
