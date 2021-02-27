from unittest import mock

from django.test import TestCase

from psct.forms import resultado as forms


class FileFormatFormTestCase(TestCase):
    def test_fields_esperados_deveriam_existir(self):
        form = forms.FileFormatForm()
        self.assertIn("render", form.fields)
        self.assertIn("filetype", form.fields)

    @mock.patch("psct.render.register.get_choices")
    def test_init_deveria_adicionar_choices_registrados_no_render(self, get_choices):
        forms.FileFormatForm()
        get_choices.assert_called_once()

    @mock.patch("psct.render.driver.get_choices")
    def test_init_deveria_adicionar_choices_registrados_no_driver(self, get_choices):
        forms.FileFormatForm()
        get_choices.assert_called_once()
