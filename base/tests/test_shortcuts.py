from unittest import mock

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import TestCase

from .. import shortcuts


class GetObjectOrPermissionDeniedTestCase(TestCase):

    @mock.patch("base.shortcuts.get_object_or_404")
    def test_deveria_pegar_objeto_com_parametros_validos(self, get_object_or_404):
        expected_instance = mock.Mock()
        get_object_or_404.return_value = expected_instance
        klass = mock.Mock()
        self.assertEqual(expected_instance, shortcuts.get_object_or_permission_denied(klass, id=1))

    @mock.patch("base.shortcuts.get_object_or_404")
    def test_deveria_lancar_permission_denied_com_objeto_inexistente(self, get_object_or_404):
        get_object_or_404.side_effect = Http404
        klass = mock.Mock()
        with self.assertRaises(PermissionDenied):
            shortcuts.get_object_or_permission_denied(klass, id=1)
