from unittest import mock

from django.db import models
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.test import TestCase

from ..custom import field


class ResolveTypeTestCase(TestCase):

    @mock.patch("base.custom.field.get_field")
    def test_deveria_retornar_o_field_do_campo_solicitado(self, get_field):
        get_field.return_value = "FieldObject"
        self.assertEqual("FieldObject", field.resolve_type(mock.Mock(), "fieldname"))

    @mock.patch("base.custom.field.get_field")
    def test_deveria_retornar_retornar_o_field_do_related_model(self, get_field):
        get_field.return_value = mock.Mock(spec=models.ForeignKey)
        field_obj = field.resolve_type(mock.Mock(), "fieldname")
        self.assertIsInstance(field_obj, models.ForeignKey)

    @mock.patch("base.custom.field.get_field")
    def test_deveria_retornar_retornar_o_field_do_reverse_related_model(self, get_field):
        get_field.return_value = mock.Mock(spec=ForeignObjectRel)
        field_obj = field.resolve_type(mock.Mock(), "fieldname")
        self.assertIsInstance(field_obj, ForeignObjectRel)


class GetFieldTestCase(TestCase):

    def test_deveria_pegar_field_a_partir_do_meta_do_model(self):
        model_class = mock.Mock(spec=models.Model)
        model_class._meta = mock.Mock()
        model_class._meta.get_field.return_value = mock.Mock(models.Field)
        self.assertIsInstance(field.get_field(model_class, "fieldname"), models.Field)


class GetModelFromFieldTestCase(TestCase):

    def test_deveria_pegar_model_do_field(self):
        field_obj = mock.Mock(spec=models.Field)
        field_obj.model = "Model"
        self.assertEqual("Model", field.get_model_from_field(field_obj))

    def test_deveria_pegar_model_do_field_quando_foreign_key(self):
        field_obj = mock.Mock(spec=models.ForeignKey)
        field_obj.related_model = "Model"
        self.assertEqual("Model", field.get_model_from_field(field_obj))

    def test_deveria_pegar_model_do_field_quando_ha_relacionamento_reverso(self):
        field_obj = mock.Mock(spec=ForeignObjectRel)
        field_obj.field = mock.Mock()
        field_obj.field.model = "Model"
        self.assertEqual("Model", field.get_model_from_field(field_obj))


class GetVerboseNameTestCase(TestCase):
    def test_deveria_pegar_o_verbose_name_a_partir_do_meta_options_do_modelo(self):
        model_instance = mock.Mock(spec=models.Model)
        model_instance._meta = mock.Mock()
        model_instance._meta.verbose_name = "Model name"
        self.assertEqual("Model name", field.get_verbose_name(model_instance))

    def test_deveria_retornar_nome_da_classe_se_nao_houver_verbose_name(self):
        model_instance = mock.Mock(spec=models.Model)
        model_instance.__name__ = "model"
        model_instance._meta = mock.MagicMock(spec=dict)
        self.assertEqual("Model", field.get_verbose_name(model_instance))


class GetVerboseNamePluralTestCase(TestCase):
    def test_deveria_pegar_o_verbose_name_plural_a_partir_do_meta_options_do_modelo(self):
        model_instance = mock.Mock(spec=models.Model)
        model_instance._meta = mock.Mock()
        model_instance._meta.verbose_name_plural = "Model name"
        self.assertEqual("Model name", field.get_verbose_name_plural(model_instance))

    def test_deveria_retornar_nome_da_classe_se_nao_houver_verbose_name_plural(self):
        model_instance = mock.Mock(spec=models.Model)
        model_instance.__name__ = "model"
        model_instance._meta = mock.MagicMock(spec=dict)
        self.assertEqual("Model", field.get_verbose_name_plural(model_instance))


class GetFieldNameTestCase(TestCase):

    def test_deveria_pegar_o_verbose_name_a_partir_do_campo(self):
        field_instance = mock.Mock(spec=models.Field)
        field_instance.verbose_name = "Field name"
        self.assertEqual("Field name", field.get_field_name(field_instance))

    def test_deveria_retornar_nome_da_classe_se_nao_houver_verbose_name_plural(self):
        field_instance = mock.Mock(spec=models.Field)
        field_instance.name = "field"
        self.assertEqual("field", field.get_field_name(field_instance))
