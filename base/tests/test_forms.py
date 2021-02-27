from unittest import mock

import django.forms
from django.test import TestCase

from base import forms


class ExampleForm(forms.FieldStyledMixin, django.forms.Form):
    field_char = django.forms.CharField(max_length=1)
    field_bool = django.forms.BooleanField()


class FieldStyledMixinTestCase(TestCase):
    def test_field_class_deveria_estar_corretamente_configurado(self):
        self.assertEqual("form-control", forms.FieldStyledMixin.field_class)

    def test_styled_fields_deveria_estar_corretamente_configurado(self):
        self.assertEqual(["__all__"], forms.FieldStyledMixin.styled_fields)

    @mock.patch.object(forms.FieldStyledMixin, "apply_style")
    def test_apply_style_deveria_ser_chamado_no_init(self, apply_style):
        forms.FieldStyledMixin()
        apply_style.assert_called_once()

    def test_apply_style_deveria_aplicar_o_estilo_para_todos_os_campos(self):
        form = ExampleForm()
        self.assertEqual(["field_char"], form.styled_fields)

    def test_apply_style_deveria_aplicar_o_estilo_para_campos_definidos(self):

        class ExampleWithDefinedStyleFieldsForm(forms.FieldStyledMixin, django.forms.Form):
            field_char = django.forms.CharField(max_length=1)
            other_field_char = django.forms.CharField(max_length=1)
            field_bool = django.forms.BooleanField()

            styled_fields = ["field_char"]

        form = ExampleWithDefinedStyleFieldsForm()
        self.assertIn("field_char", form.styled_fields)
        self.assertNotIn("other_field_char", form.styled_fields)

    def test_apply_style_deveria_definir_classe_css_nos_widgets_dos_fields(self):
        form = ExampleForm()
        for field in form.styled_fields:
            self.assertEqual(form.field_class, form.fields[field].widget.attrs["class"])

    def test_apply_style_deveria_remover_campos_dos_campos_checkbox_e_radioselect(self):
        form = ExampleForm()
        self.assertNotIn("class", form.fields["field_bool"].widget.attrs)
