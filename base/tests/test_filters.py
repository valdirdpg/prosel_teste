from unittest import mock

from django import forms
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.test import TestCase
from django.db import models
from ..custom import filters


class ConcreteFilter(filters.Filter):

    def get_choices(self, queryset):
        super().get_queryset(queryset)

    def get_queryset(self, queryset):
        super().get_queryset(queryset)


class FilterTestCase(TestCase):
    def test_deveria_ter_template_name_configurado(self):
        self.assertEqual("psct/base/custom/filter.html", filters.Filter.template_name)

    def test_deveria_ter_atributo_title(self):
        self.assertTrue(hasattr(filters.Filter, "title"))

    def test_deveria_ter_atributo_parameter_name(self):
        self.assertTrue(hasattr(filters.Filter, "parameter_name"))

    def test_init_deveria_criar_atributo_request(self):
        self.assertTrue(hasattr(ConcreteFilter(mock.Mock()), "request"))

    def test_get_value_deveria_pegar_valor_a_partir_do_request_get(self):
        request = mock.Mock()
        request.GET = {"parameter": "value"}
        concrete_filter = ConcreteFilter(request)
        concrete_filter.parameter_name = "parameter"
        self.assertEqual("value", concrete_filter.get_value())

    def test_has_output_deveria_ser_falso_se_nao_ha_valor_no_choices(self):
        with mock.patch("base.tests.test_filters.ConcreteFilter.get_choices") as get_choices:
            get_choices.return_value = ()
            concrete_filter = ConcreteFilter(mock.Mock())
            self.assertFalse(concrete_filter.has_output())

    def test_has_output_deveria_ser_verdadeiro_se_ha_valor_no_choices(self):
        with mock.patch("base.tests.test_filters.ConcreteFilter.get_choices") as get_choices:
            get_choices.return_value = ("id", "value")
            concrete_filter = ConcreteFilter(mock.Mock())
            self.assertTrue(concrete_filter.has_output())

    def test_get_expected_parameters_deveria_retornar_parameter_name(self):
        concrete_filter = ConcreteFilter(mock.Mock())
        concrete_filter.parameter_name = "parameter"
        self.assertEqual(["parameter"], concrete_filter.get_expected_parameters())

    @mock.patch("base.custom.filters.render_to_string")
    def test_render_deveria_renderizar_o_template(self, render_to_string):
        render_to_string.return_value = "rendered template"
        concrete_filter = ConcreteFilter(mock.Mock())
        self.assertEqual("rendered template", concrete_filter.render())

    def test_get_context_data_deveria_retornar_dicionario(self):
        concrete_filter = ConcreteFilter(mock.Mock())
        self.assertIsInstance(concrete_filter.get_context_data(), dict)

    def test_get_context_data_deveria_retornar_dicionario_com_filter_como_chave(self):
        concrete_filter = ConcreteFilter(mock.Mock())
        self.assertIn("filter", concrete_filter.get_context_data())

    def test_get_context_data_deveria_retornar_self_na_chave_filter(self):
        concrete_filter = ConcreteFilter(mock.Mock())
        self.assertEqual(concrete_filter, concrete_filter.get_context_data()["filter"])

    @mock.patch("base.tests.test_filters.ConcreteFilter.get_choices")
    def test_get_form_field_deve_retornar_choice_field(self, get_choices):
        get_choices.return_value = (("id", "value"),)
        concrete_filter = ConcreteFilter(mock.Mock())
        self.assertIsInstance(concrete_filter.get_form_field(mock.Mock()), forms.ChoiceField)

    @mock.patch("base.tests.test_filters.ConcreteFilter.get_choices")
    def test_get_form_field_deve_retornar_choice_field_com_choices_configurado(self, get_choices):
        get_choices.return_value = (("id", "value"),)
        concrete_filter = ConcreteFilter(mock.Mock())
        self.assertEqual([("id", "value")], concrete_filter.get_form_field(mock.Mock()).choices)

    def test_get_choices_nao_eh_implementado(self):
        concrete_filter = ConcreteFilter(mock.Mock())
        with self.assertRaises(NotImplementedError):
            concrete_filter.get_choices(mock.Mock())

    def test_get_queryset_nao_eh_implementado(self):
        concrete_filter = ConcreteFilter(mock.Mock())
        with self.assertRaises(NotImplementedError):
            concrete_filter.get_queryset(mock.Mock())


class ConcreteTypedFieldFilter(filters.TypedFieldFilter):

    @classmethod
    def match(cls, obj, request):
        super().match(obj, request)

    def get_choices(self, queryset):
        super().get_choices(queryset)

    def get_title(self):
        super().get_title()

    def get_queryset(self, field_path, value, queryset):
        super().get_queryset(field_path, value, queryset)


class TypedFieldFilterTestCase(TestCase):

    def test_deveria_ter_atributo_priority(self):
        self.assertTrue(hasattr(filters.TypedFieldFilter, "priority"))

    def test_deveria_ter_atributo_has_custom_queryset(self):
        self.assertTrue(hasattr(filters.TypedFieldFilter, "has_custom_queryset"))

    def test_init_deveria_criar_atributos_field_e_request(self):
        self.assertTrue(hasattr(ConcreteFilter(mock.Mock()), "request"))

    def test_match_nao_eh_implementado(self):
        with self.assertRaises(NotImplementedError):
            ConcreteTypedFieldFilter.match(mock.Mock(), mock.Mock())

    def test_get_choices_nao_eh_implementado(self):
        concrete_filter = ConcreteTypedFieldFilter(mock.Mock(), mock.Mock())
        with self.assertRaises(NotImplementedError):
            concrete_filter.get_choices(mock.Mock())

    def test_get_queryset_nao_eh_implementado(self):
        concrete_filter = ConcreteTypedFieldFilter(mock.Mock(), mock.Mock())
        with self.assertRaises(NotImplementedError):
            concrete_filter.get_queryset(mock.Mock(), mock.Mock(), mock.Mock())

    def test_get_title_nao_eh_implementado(self):
        concrete_filter = ConcreteTypedFieldFilter(mock.Mock(), mock.Mock())
        with self.assertRaises(NotImplementedError):
            concrete_filter.get_title()


class FieldFilterTestCase(TestCase):

    def test_deveria_ter_atributo__register(self):
        self.assertTrue(hasattr(filters.FieldFilter, "_register"))

    @mock.patch.object(filters.FieldFilter, "get_typed_filter")
    @mock.patch("base.custom.filters.field")
    def test_init_deveria_preencher_model(self, field, get_typed_filter):
        model = mock.Mock(spec=models.Model)
        field_filter = filters.FieldFilter(model, mock.Mock(), mock.Mock())
        self.assertEqual(model, field_filter.model)

    @mock.patch("base.custom.filters.field")
    @mock.patch("base.custom.filters.FieldFilter.get_typed_filter")
    def test_init_deveria_definir_titulo_a_partir_do_filtro_definido(self, get_typed_filter, field):
        get_typed_filter.return_value.get_title.return_value = "Title"
        field_filter = filters.FieldFilter(mock.Mock(), mock.Mock(), mock.Mock())
        self.assertEqual("Title", field_filter.title)

    @mock.patch("base.custom.filters.field.resolve_type")
    @mock.patch("base.custom.filters.FieldFilter.get_typed_filter")
    def test_init_deveria_definir_titulo_a_partir_do_field(self, get_typed_filter, resolve_type):
        get_typed_filter.return_value = False
        resolve_type.return_value.verbose_name.title.return_value = "Field title"
        field_filter = filters.FieldFilter(mock.Mock(), mock.Mock(), mock.Mock())
        self.assertEqual("Field title", field_filter.title)

    @mock.patch("base.custom.filters.field.resolve_type")
    @mock.patch("base.custom.filters.FieldFilter.get_typed_filter")
    def test_get_choices_deveria_obter_valores_a_partir_do_filter(self, get_typed_filter, resolve_type):
        get_typed_filter.return_value.get_choices.return_value = ("id", "value")
        field_filter = filters.FieldFilter(mock.Mock(), mock.Mock(), mock.Mock())
        self.assertEqual(("id", "value"), field_filter.get_choices(mock.Mock()))

    @mock.patch("base.custom.filters.field.resolve_type")
    @mock.patch.object(filters.FieldFilter, "get_typed_filter")
    def test_get_choices_deveria_obter_valores_a_partir_do_choice(self, get_typed_filter, resolve_type):
        get_typed_filter.return_value = False
        resolve_type.return_value.get_choices.return_value = ("id", "value")
        field_filter = filters.FieldFilter(mock.Mock(), mock.Mock(), mock.Mock())
        self.assertEqual(("id", "value"), field_filter.get_choices(mock.Mock()))

    @mock.patch("base.custom.filters.field.resolve_type")
    @mock.patch.object(filters.FieldFilter, "get_typed_filter")
    def test_get_choices_deveria_obter_valores_a_partir_do_queryset(self, get_typed_filter, resolve_type):
        resolve_type.return_value.get_choices.side_effect = AttributeError
        get_typed_filter.return_value = False
        field_filter = filters.FieldFilter(mock.Mock(), mock.Mock(), mock.Mock())
        queryset = mock.Mock()
        queryset.values_list.return_value.distinct.return_value = ["1"]
        self.assertEqual([("1", "1")], field_filter.get_choices(queryset))

    @mock.patch("base.custom.filters.field.resolve_type")
    @mock.patch.object(filters.FieldFilter, "get_typed_filter")
    def test_get_queryset_deveria_ser_o_mesmo_se_nao_houver_value(self, get_typed_filter, resolve_type):
        request = mock.Mock()
        request.GET = {}
        field_filter = filters.FieldFilter(mock.Mock(), mock.Mock(), request)
        queryset = mock.Mock()
        self.assertEqual(queryset, field_filter.get_queryset(queryset))

    @mock.patch("base.custom.filters.field.resolve_type")
    def test_get_typed_filter_deveria_ser_nulo_se_registro_estiver_vazio(self, resolve_type):
        field_filter = filters.FieldFilter(mock.Mock(), mock.Mock(), mock.Mock())
        self.assertIsNone(field_filter.get_typed_filter())


class RelatedObjectFieldTestCase(TestCase):
    def test_match_deveria_ser_verdadeiro_se_o_obj_eh_a_instancia_esperada(self):
        filter_object = filters.RelatedObjectField(mock.Mock(), mock.Mock())
        compared_object = mock.Mock(spec=ForeignObjectRel)
        self.assertTrue(filter_object.match(compared_object, mock.Mock()))

    @mock.patch("base.custom.filters.field.get_verbose_name")
    def test_get_title_deveria_pegar_a_partir_do_field(self, get_verbose_name):
        get_verbose_name.return_value = "Verbose name from field"
        filter_object = filters.RelatedObjectField(mock.Mock(), mock.Mock())
        self.assertEqual("Verbose name from field", filter_object.get_title())

    def test_get_choices_deveria_pegar_a_partir_do_field(self):
        field = mock.Mock()
        field.get_choices.return_value = ("id", "value")
        filter_object = filters.RelatedObjectField(field, mock.Mock())
        self.assertEqual(("id", "value"), filter_object.get_choices(mock.Mock()))


class BooleanFieldFilterTestCase(TestCase):
    def test_match_deveria_ser_verdadeiro_se_o_obj_eh_a_instancia_esperada(self):
        filter_object = filters.BooleanFieldFilter(mock.Mock(), mock.Mock())
        compared_object = mock.Mock(spec=models.BooleanField)
        self.assertTrue(filter_object.match(compared_object, mock.Mock()))

    def test_get_title_deveria_pegar_a_partir_do_field(self):
        field = mock.Mock()
        field.verbose_name = "Verbose name from boolean field"
        filter_object = filters.BooleanFieldFilter(field, mock.Mock())
        self.assertEqual("Verbose name from boolean field", filter_object.get_title())

    def test_get_choices_deveria_pegar_a_partir_do_field(self):
        filter_object = filters.BooleanFieldFilter(mock.Mock(), mock.Mock())
        self.assertEqual([("", "---------"), ("0", "Não"), ("1", "Sim")], filter_object.get_choices(mock.Mock()))


class AutoCompleteFilterTestCase(TestCase):

    @mock.patch("base.custom.filters.AutoCompleteFilter.check_field_path")
    def test_init_parameter_name(self, check_field_path):
        lookup = mock.MagicMock()
        lookup.model.__name__ = "Name"
        field_filter = filters.AutoCompleteFilter(mock.Mock(), lookup)
        self.assertEqual("autocomplete_name", field_filter.parameter_name)

    @mock.patch("base.custom.filters.AutoCompleteFilter.check_field_path")
    def test_init_title(self, check_field_path):
        lookup = mock.MagicMock()
        lookup.model.__name__ = "Name"
        lookup.title = "Title"
        field_filter = filters.AutoCompleteFilter(mock.Mock(), lookup)
        self.assertEqual("Title", field_filter.title)

    @mock.patch("base.custom.filters.AutoCompleteFilter.check_field_path")
    @mock.patch("base.custom.filters.field.get_verbose_name")
    def test_init_title_field_verbose_name(self, get_verbose_name, check_field_path):
        get_verbose_name.return_value = "Verbose name"
        lookup = mock.MagicMock()
        lookup.model.__name__ = "Name"
        lookup.title = ""
        field_filter = filters.AutoCompleteFilter(mock.Mock(), lookup)
        self.assertEqual("Verbose name", field_filter.title)

    @mock.patch("base.custom.filters.field.resolve_type")
    def test_check_field_path(self, resolve_type):
        resolve_type.return_value = mock.Mock(spec=models.ForeignKey)
        lookup = mock.MagicMock()
        lookup.model.__name__ = "Name"
        field_filter = filters.AutoCompleteFilter(mock.Mock(), lookup)
        self.assertIsNone(field_filter.check_field_path(mock.Mock()))

    @mock.patch("base.custom.filters.field.resolve_type")
    def test_check_field_path_raise_exception(self, resolve_type):
        resolve_type.return_value = mock.Mock(spec=models.CharField)
        lookup = mock.MagicMock()
        lookup.model.__name__ = "Name"
        with self.assertRaises(ValueError):
            filters.AutoCompleteFilter(mock.Mock(), lookup)

    @mock.patch("base.custom.filters.AutoCompleteFilter.check_field_path")
    @mock.patch("base.custom.filters.field.resolve_type")
    def test_get_choices_deveria_ser_vazio(self, resolve_type, check_field_path):
        lookup = mock.MagicMock()
        lookup.model.__name__ = "Name"
        field_filter = filters.AutoCompleteFilter(mock.Mock(), lookup)
        self.assertEqual([], field_filter.get_choices(mock.Mock()))
