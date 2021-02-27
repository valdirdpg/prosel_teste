from unittest import mock

from django.test import TestCase
from suaprest import SuapError

from base import lookups


class ServidorLookupTestCase(TestCase):
    def test_get_result_deveria_retornar_str_do_obj(self):
        lookup = lookups.ServidorLookup()
        self.assertEqual("a", lookup.get_result("a"))

    @mock.patch.object(lookups.ServidorLookup, "format_item_display")
    def test_format_match_deveria_obter_valor_a_partir_do_format_item_display(self,
                                                                              format_item_display):
        format_item_display.return_value = mock.Mock()
        lookup = lookups.ServidorLookup()
        self.assertEqual(format_item_display(), lookup.format_match(mock.Mock()))

    @mock.patch.object(lookups.ServidorLookup, "get_result")
    def test_format_item_display_deveria_obter_valor_a_partir_do_format_item_display(self,
                                                                                     get_result):
        get_result.return_value = mock.Mock()
        lookup = lookups.ServidorLookup()
        self.assertEqual(get_result(), lookup.format_item_display(mock.Mock()))

    @mock.patch("base.lookups.Client")
    @mock.patch("base.lookups.Servidor")
    def test_get_objects_deveria_retornar_lista_de_servidores(self, servidor, client):
        servidor.return_value = mock.Mock()
        client.return_value.get_servidores.return_value = [servidor()]
        lookup = lookups.ServidorLookup()
        self.assertEqual([servidor()], lookup.get_objects([1, 2, 3]))

    @mock.patch("base.lookups.Client")
    def test_get_objects_deveria_retornar_vazio_quando_ha_erro_no_suap(self, client):
        client.return_value.get_servidores.side_effect = SuapError(mock.Mock())
        lookup = lookups.ServidorLookup()
        self.assertEqual([], lookup.get_objects([1, 2, 3]))

    def test_get_objects_deveria_retornar_vazio_quando_ids_nao_forem_informados(self):
        lookup = lookups.ServidorLookup()
        self.assertEqual([], lookup.get_objects([]))

    @mock.patch("base.lookups.Client")
    def test_get_query_deveria_retornar_vazio_quando_ha_erro_no_suap(self, client):
        client.return_value.search_servidores.side_effect = SuapError(mock.Mock())
        lookup = lookups.ServidorLookup()
        self.assertEqual([], lookup.get_query(mock.Mock(), mock.Mock()))

    @mock.patch("base.lookups.Client")
    @mock.patch("base.lookups.Servidor")
    def test_get_query_deveria_retornar_lista_de_servidores(self, servidor, client):
        servidor.return_value = mock.Mock()
        client.return_value.search_servidores.return_value = [servidor()]
        lookup = lookups.ServidorLookup()
        self.assertEqual([servidor()], lookup.get_query(mock.Mock(), mock.Mock()))
