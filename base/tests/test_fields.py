from unittest import mock

from django.core.exceptions import ValidationError
from django.db import models
from django.test import TestCase

from base import fields


class SafeReCaptchaFieldTestCase(TestCase):

    @mock.patch.object(fields.ReCaptchaField, "clean")
    def test_clean_deveria_retornar_valores_do_super(self, clean):
        clean.return_value = {"example_field": 1}
        field = fields.SafeReCaptchaField()
        self.assertDictEqual({"example_field": 1}, field.clean(mock.Mock()))

    @mock.patch.object(fields.ReCaptchaField, "clean")
    def test_clean_deveria_transformar_key_error_em_validation_error(self, clean):
        clean.side_effect = KeyError
        field = fields.SafeReCaptchaField()
        with self.assertRaises(ValidationError):
            field.clean(mock.Mock())


class ModelChoiceCustomLabelFieldTestCase(TestCase):

    def test_init_deveria_obter_label_from_instance_func_do_kwargs(self):
        func = mock.Mock()
        field = fields.ModelChoiceCustomLabelField(
            queryset=mock.Mock(spec=models.QuerySet),
            label_from_instance_func=func
        )
        self.assertTrue(hasattr(field, "label_from_instance_func"))
        self.assertEqual(func, field.label_from_instance_func)

    def test_label_from_instance_deveria_chamar_label_from_instance_func(self):
        func = mock.Mock()
        func.return_value = "Label"
        field = fields.ModelChoiceCustomLabelField(
            queryset=mock.Mock(spec=models.QuerySet),
            label_from_instance_func=func
        )
        obj = mock.Mock()
        self.assertEqual("Label", field.label_from_instance(obj))
        func.assert_called_with(obj)


class ModelMultipleChoiceFieldTestCase(TestCase):

    def test_init_deveria_obter_label_from_instance_func_do_kwargs(self):
        func = mock.Mock()
        field = fields.ModelMultipleChoiceField(
            queryset=mock.Mock(spec=models.QuerySet),
            label_from_instance_func=func
        )
        self.assertTrue(hasattr(field, "label_from_instance_func"))
        self.assertEqual(func, field.label_from_instance_func)

    def test_label_from_instance_func_deveria_ser_opcional(self):
        field = fields.ModelMultipleChoiceField(queryset=mock.Mock(spec=models.QuerySet))
        self.assertTrue(hasattr(field, "label_from_instance_func"))
        self.assertIsNone(field.label_from_instance_func)

    def test_label_from_instance_deveria_chamar_label_from_instance_func(self):
        func = mock.Mock()
        func.return_value = "Label"
        field = fields.ModelMultipleChoiceField(
            queryset=mock.Mock(spec=models.QuerySet),
            label_from_instance_func=func
        )
        obj = mock.Mock()
        self.assertEqual("Label", field.label_from_instance(obj))
        func.assert_called_with(obj)

    @mock.patch.object(fields.forms.ModelMultipleChoiceField, "label_from_instance")
    def test_label_from_instance_deveria_chamar_label_from_instance_na_super_classe(
            self, label_from_instance
    ):
        label_from_instance.return_value = "Label"
        field = fields.ModelMultipleChoiceField(
            queryset=mock.Mock(spec=models.QuerySet),
        )
        obj = mock.Mock()
        self.assertEqual("Label", field.label_from_instance(obj))
        label_from_instance.assert_called_with(obj)
