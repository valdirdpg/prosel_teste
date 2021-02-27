from unittest import expectedFailure, mock

from django.core.exceptions import FieldDoesNotExist
from django.http import Http404
from django.test import TestCase

from ..custom.views import listview


class GetMethodNameTestCase(TestCase):
    def test_deveria_obter_valor_do_short_description_caso_exista(self):
        def example():
            pass

        example.short_description = "Title"
        self.assertEqual("Title", listview.get_method_name(example))

    def test_deveria_retornar_name_como_titulo_quando_nao_houver_short_description(self):
        def example():
            pass

        self.assertEqual("Example", listview.get_method_name(example))


class ListViewFormTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.view = mock.Mock()
        self.view.has_tabs = mock.Mock()
        self.view.get_filters = mock.MagicMock()
        self.view.get_search_fields = mock.Mock()

    def test_field_class_deveria_ter_valor_padrao(self):
        self.assertEqual(listview.ListViewForm.field_class, "form-control filter-form")

    def test_has_tabs_deveria_criar_campo_tab(self):
        self.view.has_tabs.return_value = True
        form = listview.ListViewForm(view=self.view)
        self.assertIn('tab', form.fields)

    def test_campo_tab_criado_no_init_deveria_ser_oculto(self):
        self.view.has_tabs.return_value = True
        form = listview.ListViewForm(view=self.view)
        campo_tab = form.fields["tab"]
        self.assertTrue(campo_tab.widget.is_hidden)

    def test_campo_tab_criado_no_init_deveria_ter_valor_initial_do_request_params(self):
        self.view.has_tabs.return_value = True
        self.view.request.GET = {"tab": "tab value"}
        form = listview.ListViewForm(view=self.view)
        campo_tab = form.fields["tab"]
        self.assertEqual("tab value", campo_tab.initial)

    @mock.patch.object(listview.ListViewForm, "apply_style")
    def test_deveria_criar_campo_a_partir_do_filters_da_view(self, apply_style):
        filter_example = mock.Mock()
        filter_example.parameter_name = "param"
        filter_example.get_form_field.return_value = mock.Mock()
        self.view.get_filters.return_value = [filter_example]
        self.view.request.GET = {"param": "value"}
        form = listview.ListViewForm(view=self.view)
        self.assertEqual("value", form.fields["param"].initial)

    def test_deveria_criar_campo_busca_se_view_tem_search_fields(self):
        self.view.get_search_fields.return_value = True
        form = listview.ListViewForm(view=self.view)
        self.assertIn("q", form.fields)

    def test_campo_busca_deveria_ter_valor_inicial_do_request_param(self):
        self.view.get_search_fields.return_value = True
        self.view.request.GET = {"q": "value"}
        form = listview.ListViewForm(view=self.view)
        self.assertEqual("value", form.fields["q"].initial)


class ColumnTestCase(TestCase):
    @mock.patch.object(listview.Column, "resolve_name")
    def test_init_deveria_preencher_atributo_name(self, resolve_name):
        resolve_name.return_value = "Name"
        self.assertEqual("Name", listview.Column("Name", mock.Mock()).name)

    @mock.patch("base.custom.views.listview.m_field")
    def test_resolve_name_deveria_buscar_a_partir_do_attribute_name(self, field):
        field.resolve_type = mock.Mock()
        field.get_field_name.return_value = "Expected name"
        column = listview.Column(mock.Mock(), mock.Mock())
        self.assertEqual("Expected name", column.resolve_name(mock.Mock(), mock.Mock()))

    @mock.patch("base.custom.views.listview.m_field")
    def test_resolve_name_deveria_buscar_a_partir_do_short_description(self, field):
        field.resolve_type.side_effect = FieldDoesNotExist
        view = mock.Mock()
        view.method = lambda: True
        view.method.short_description = "Method name"
        self.assertEqual("Method name", listview.Column.resolve_name("method", view))

    @mock.patch("base.custom.views.listview.m_field")
    def test_resolve_name_deveria_lancar_erro_caso_atributo_nao_exista(self, field):
        field.resolve_type.side_effect = FieldDoesNotExist
        view = mock.Mock()
        delattr(view, "method")
        with self.assertRaises(AttributeError):
            listview.Column.resolve_name("method", view)


class ObjectDataTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.view = mock.Mock()
        self.obj = mock.Mock()
        self.object_data = listview.ObjectData(self.view, self.obj)

    def test_get_field_value_deveria_retornar_valor_pelo_field(self):
        self.obj.field = "Field value"
        self.assertEqual("Field value", self.object_data.get_field_value("field"))

    def test_get_method_value_deveria_retornar_valor_pelo_metodo(self):
        self.view.method.return_value = "Value from method"
        self.assertEqual("Value from method", self.object_data.get_method_value("method"))

    def test_get_column_value_deveria_pegar_valor_a_partir_do_get_field_value(self):
        self.obj.field = "Field value"
        self.assertEqual("Field value", self.object_data.get_column_value("field"))

    def test_get_column_value_deveria_pegar_valor_a_partir_do_get_method_value(self):
        delattr(self.obj, "method")
        self.view.method.return_value = "Value from method"
        self.assertEqual("Value from method", self.object_data.get_column_value("method"))

    def test_get_column_value_deveria_lancar_excecao_quando_nao_puder_retornar_valor(self):
        delattr(self.obj, "method")
        delattr(self.view, "method")
        with self.assertRaises(AttributeError):
            self.object_data.get_column_value("method")

    @mock.patch.object(listview.ObjectData, "get_column_value")
    def test_iter_deveria_retornar_valores_a_partir_de_list_display(self, get_column_value):
        get_column_value.return_value = "a"
        self.view.get_list_display.return_value = ["a"]
        object_data = listview.ObjectData(self.view, self.obj)
        itens = [item for item in object_data]
        self.assertListEqual(["a"], itens)

    def test_iter_deveria_retornar_obj_se_list_display_for_vazio(self):
        self.view.get_list_display.return_value = []
        object_data = listview.ObjectData(self.view, self.obj)
        self.assertListEqual([self.obj], [item for item in object_data])


class ListViewTestCase(TestCase):
    def test_template_name_deveria_estar_configurado(self):
        self.assertEqual("base/listview.html", listview.ListView.template_name)

    def test_paginate_by_deveria_ter_valor_padrao_vinte_e_cinco(self):
        self.assertEqual(25, listview.ListView.paginate_by)

    def test_init_deveria_inicializar_cache_queryset_vazia(self):
        self.assertIsNone(listview.ListView()._cache_queryset)

    def test_init_deveria_inicializar_cache_filters_vazia(self):
        self.assertIsNone(listview.ListView()._filters_cache)

    def test_get_autocomplete_fields_deveria_retornar_valor_do_atributo(self):
        self.assertEqual(
            listview.ListView.autocomplete_fields,
            listview.ListView().get_autocomplete_fields()
        )

    def test_has_autocomplete_fields_deveria_verificar_se_ha_itens_definidos(self):
        self.assertFalse(listview.ListView().has_autocomplete_fields())

    def test_get_search_fields_deveria_retornar_valor_do_atributo(self):
        self.assertEqual(
            tuple(listview.ListView.search_fields),
            listview.ListView().get_search_fields()
        )

    def test_has_search_fields_deveria_verificar_se_ha_itens_definidos(self):
        self.assertFalse(listview.ListView().has_search_fields())

    def test_get_list_display_deveria_retornar_valor_do_atributo(self):
        self.assertEqual(
            tuple(listview.ListView.list_display),
            listview.ListView().get_list_display()
        )

    @mock.patch.object(listview.Column, "resolve_name")
    def test_get_columns_deveria_retornar_uma_lista_a_partir_do_list_diplay(self, resolve_name):
        resolve_name.return_value = "Field"
        view = listview.ListView()
        view.list_display = ["Field"]
        self.assertListEqual(
            [listview.Column("Field", view)],
            view.get_columns()
        )

    @mock.patch.object(listview.Column, "resolve_name")
    def test_get_column_deveria_retornar_objeto_column(self, resolve_name):
        resolve_name.return_value = "Field"
        view = listview.ListView()
        self.assertEqual(
            listview.Column("Field", view),
            view.get_column("Field")
        )

    def test_get_object_columns_deveria_retornar_object_data(self):
        view = listview.ListView()
        obj = mock.Mock()
        self.assertIsInstance(view.get_object_columns(obj), listview.ObjectData)

    def test_get_simple_filters_deveria_retornar_valor_do_atributo(self):
        self.assertEqual(
            tuple(listview.ListView.simple_filters),
            listview.ListView().get_simple_filters()
        )

    def test_get_field_filters_deveria_retornar_valor_do_atributo(self):
        self.assertEqual(
            tuple(listview.ListView.field_filters),
            listview.ListView().get_field_filters()
        )

    def test_has_filter_deveria_verificar_se_ha_itens_definidos(self):
        self.assertFalse(listview.ListView().has_filter())

    def test_get_filters_deveria_retornar_valor_do_cache(self):
        view = listview.ListView()
        view._filters_cache = mock.Mock()
        self.assertEqual(view._filters_cache, view.get_filters())

    def test_get_filters_deveria_retornar_valor_de_simple_filters(self):
        view = listview.ListView()
        view.request = mock.Mock()
        filter_object = mock.Mock()
        filter_object.return_value = "Filter"
        view.simple_filters = [filter_object]
        self.assertIn("Filter", view.get_filters())

    @mock.patch("base.custom.views.listview.FieldFilter")
    def test_get_filters_deveria_retornar_valor_de_field_filters(self, field_filter):
        view = listview.ListView()
        view.request = mock.Mock()
        field_filter.return_value = "Filter"
        view.field_filters = [field_filter]
        self.assertIn("Filter", view.get_filters())

    @mock.patch("base.custom.views.listview.AutoCompleteFilter")
    def test_get_filters_deveria_retornar_valor_de_autocomplete_fields(self, field_filter):
        view = listview.ListView()
        view.request = mock.Mock()
        field_filter.return_value = "Filter"
        view.autocomplete_fields = [field_filter]
        self.assertIn("Filter", view.get_filters())

    @mock.patch("base.custom.views.listview.ListView.get_filters")
    def test_has_any_filter_set_deveria_retornar_se_ha_valor_em_um_dos_filtros(self, get_filters):
        filter_object = mock.Mock()
        filter_object.return_value = "Filter"
        filter_object.get_value.return_value = True
        get_filters.return_value = [filter_object]
        view = listview.ListView()
        self.assertTrue(view.has_any_filter_set())

    @mock.patch("base.custom.views.listview.ListView.get_filters")
    @mock.patch("base.custom.views.listview.ListView._requires_search_query")
    def test_has_any_filter_set_deveria_retornar_se_ha_valor_em_um_dos_filtros(
            self, _requires_search_query, get_filters
    ):
        _requires_search_query.return_value = True
        get_filters.return_value = []
        view = listview.ListView()
        self.assertTrue(view.has_any_filter_set())

    def test_get_always_show_form_deveria_retornar_valor_do_atributo(self):
        self.assertEqual(
            listview.ListView.always_show_form,
            listview.ListView().get_always_show_form()
        )

    @mock.patch.object(listview.ListView, "has_any_filter_set")
    def test_should_display_form_deveria_verifiar_has_any_filter_set(self, has_any_filter_set):
        has_any_filter_set.return_value = True
        view = listview.ListView()
        self.assertTrue(view.should_display_form())

    @mock.patch.object(listview.ListView, "get_always_show_form")
    def test_should_display_form_deveria_verifiar_get_always_show_form(self, get_always_show_form):
        get_always_show_form.return_value = True
        view = listview.ListView()
        self.assertTrue(view.should_display_form())

    def test_get_queryset_deveria_retornar_valor_do_cache(self):
        view = listview.ListView()
        view._cache_queryset = mock.Mock()
        self.assertEqual(view._cache_queryset, view._get_queryset())

    @mock.patch("base.custom.views.listview.generic.ListView.get_queryset")
    @mock.patch.object(listview.ListView, "get_filters")
    def test_get_queryset_deveria_retornar_valor_de_filters(self, get_filters, get_queryset):
        view = listview.ListView()
        filter_object = mock.Mock()
        filter_object.get_queryset.return_value.distinct.return_value = "Filtered value"
        get_filters.return_value = [filter_object]
        self.assertIn("Filtered value", view._get_queryset())

    @mock.patch.object(listview.ListView, "has_search_fields")
    def test_requires_search_query_deveria_verificar_has_search_fields_e_querystring(
            self, has_search_fields
    ):
        has_search_fields.return_value = True
        view = listview.ListView()
        view.request = mock.Mock()
        view.request.GET = {"q": "Value"}
        self.assertTrue(view._requires_search_query())

    @mock.patch.object(listview.ListView, "get_title")
    @mock.patch("base.custom.views.listview.generic.ListView.get_context_data")
    def test_get_context_data_deveria_ter_chave_titulo(self, get_context_data, get_title):
        get_context_data.return_value = {}
        get_title.return_value = mock.Mock()
        view = listview.ListView()
        self.assertIn("titulo", view.get_context_data())

    @mock.patch.object(listview.ListView, "get_title")
    @mock.patch("base.custom.views.listview.generic.ListView.get_context_data")
    def test_get_context_data_deveria_ter_valor_do_get_title(self, get_context_data, get_title):
        get_context_data.return_value = {}
        get_title.return_value = "Title"
        view = listview.ListView()
        self.assertEqual("Title", view.get_context_data()["titulo"])

    @mock.patch.object(listview.ListView, "get_title")
    @mock.patch("base.custom.views.listview.generic.ListView.get_context_data")
    def test_get_context_data_deveria_ter_chave_view(self, get_context_data, get_title):
        get_context_data.return_value = {}
        get_title.return_value = mock.Mock()
        view = listview.ListView()
        view.object_list = mock.Mock()
        self.assertIn("view", view.get_context_data())

    @mock.patch.object(listview.ListView, "get_title")
    @mock.patch("base.custom.views.listview.generic.ListView.get_context_data")
    def test_get_context_data_deveria_ter_valor_vew(self, get_context_data, get_title):
        get_context_data.return_value = {}
        get_title.return_value = mock.Mock()
        view = listview.ListView()
        view.object_list = mock.Mock()
        self.assertEqual(view, view.get_context_data()["view"])

    @mock.patch.object(listview.ListView, "get_title")
    @mock.patch.object(listview.ListView, "has_filter")
    @mock.patch.object(listview.ListView, "has_search_fields")
    @mock.patch("base.custom.views.listview.ListViewForm")
    @mock.patch("base.custom.views.listview.generic.ListView.get_context_data")
    def test_get_context_data_deveria_ter_valor_form(
            self, get_context_data, form, has_search_fields, has_filter, get_title
    ):
        get_context_data.return_value = {}
        form.return_value = mock.Mock()
        get_title.return_value = mock.Mock()
        has_search_fields.return_value = True
        view = listview.ListView()
        view.object_list = mock.Mock()
        self.assertIn("form", view.get_context_data())

    @mock.patch.object(listview.ListView, "get_title")
    @mock.patch.object(listview.ListView, "has_filter")
    @mock.patch.object(listview.ListView, "has_search_fields")
    @mock.patch.object(listview.ListView, "get_breadcrumb")
    @mock.patch("base.custom.views.listview.BreadCrumb")
    @mock.patch("base.custom.views.listview.ListViewForm")
    @mock.patch("base.custom.views.listview.generic.ListView.get_context_data")
    def test_get_context_data_deveria_ter_valor_breadcrumb(
            self, get_context_data, form, breadcrumb, get_breadcrumb,
            has_search_fields, has_filter, get_title
    ):
        get_context_data.return_value = {}
        get_breadcrumb.return_value = ["any value"]
        view = listview.ListView()
        view.object_list = mock.Mock()
        self.assertIn("breadcrumb", view.get_context_data())

    @mock.patch.object(listview.m_field, "get_verbose_name_plural")
    def test_get_title_deveria_pegar_valor_do_verbose_name_plural(self, get_verbose_name_plural):
        get_verbose_name_plural.return_value = "Verbose name from model"
        view = listview.ListView()
        self.assertEqual("Verbose name from model", view.get_title())

    def test_get_tabs_deveria_retornar_valor_do_atributo(self):
        self.assertEqual(
            tuple(listview.ListView.tabs),
            listview.ListView().get_tabs()
        )

    def test_has_tabs_deveria_verificar_se_ha_itens_definidos(self):
        self.assertFalse(listview.ListView().has_tabs())

    @mock.patch.object(listview.ListView, "_get_queryset")
    def test_get_queryset_chamar_o_metodo_tab_definido(self, _get_queryset):
        view = listview.ListView()
        view.tab_method = mock.Mock()
        view.tab_method.return_value = mock.Mock()
        self.assertEqual(view.tab_method(), view.get_tab_queryset("tab_method"))

    @mock.patch.object(listview.ListView, "_get_method_name")
    def test_get_tab_names_deveria_ter_nome_e_descricao_das_tabs(self, _get_method_name):
        _get_method_name.return_value = "Tab description"
        view = listview.ListView()
        view.tabs = ["tab_method"]
        self.assertEqual([("tab_method", "Tab description")], view.get_tab_names())

    def test_get_method_name_deveria_retornar_o_valor_do_short_description(self):
        def example_method():
            pass

        example_method.short_description = "Description"
        view = listview.ListView()
        view.method = example_method
        self.assertEqual("Description", view._get_method_name("method"))

    def test_get_tab_deveria_lancar_404_se_nao_existir(self):
        view = listview.ListView()
        view.request = mock.Mock()
        view.request.GET = {"tab": "inexistent-tab"}
        with self.assertRaises(Http404):
            view.get_tab()

    @expectedFailure
    def test_get_tab_deveria_retornar_none_se_nao_houver_tab_no_request(self):
        # não há aba na view nem o request tem o parâmetro.
        view = listview.ListView()
        view.request = mock.Mock()
        view.request.GET = {}
        self.assertIsNone(view.get_tab())

    def test_get_tab_deveria_retornar_primeira_aba(self):
        # há aba na view, mas o request não tem o parâmetro.
        view = listview.ListView()
        view.request = mock.Mock()
        view.request.GET = {}
        view.tabs = ["tab_name"]
        self.assertEqual("tab_name", view.get_tab())

    @mock.patch.object(listview.ListView, "_get_queryset")
    def test_get_queryset_deveria_retornar_queryset_padrao(self, _get_queryset):
        _get_queryset.return_value = mock.Mock()
        view = listview.ListView()
        self.assertEqual(_get_queryset(), view.get_queryset())

    @mock.patch.object(listview.ListView, "get_tab_queryset")
    def test_get_queryset_deveria_retornar_queryset_da_aba(self, get_tab_queryset):
        get_tab_queryset.return_value = mock.Mock()
        view = listview.ListView()
        view.request = mock.Mock()
        view.request.GET = {}
        view.tabs = ["tab"]
        self.assertEqual(view.get_tab_queryset("tab"), view.get_queryset())
        get_tab_queryset.assert_called_with("tab")

    def test_get_menu_class_deveria_retornar_valor_do_atributo(self):
        self.assertEqual(
            listview.ListView.menu_class,
            listview.ListView().get_menu_class()
        )

    def test_get_button_area_deveria_retornar_lista_vazia(self):
        self.assertEqual(
            [],
            listview.ListView().get_button_area()
        )

    def test_dispatch_deveria_criar_atributo_user_a_partir_do_request(self):
        view = listview.ListView()
        view.request = mock.Mock()
        view.request.user = mock.Mock()
        view.dispatch(request=view.request)
        self.assertTrue(hasattr(view, "user"))
        self.assertEqual(view.request.user, view.user)

    @mock.patch("base.custom.views.listview.ProfileChecker")
    def test_dispatch_deveria_criar_atributo_profile_quando_checker_estiver_configurado(
            self, profile_checker
    ):
        profile_checker.return_value = mock.Mock(spec=listview.ProfileChecker)
        view = listview.ListView()
        view.request = mock.Mock()
        view.request.user = mock.Mock()
        view.profile_checker = mock.Mock()
        view.dispatch(request=mock.Mock())
        self.assertTrue(hasattr(view, "profile"))
        self.assertEqual(profile_checker(), view.profile)

    def test_get_number_label(self):
        self.assertEqual("#", listview.ListView().get_number_label())

    def test_get_show_numbers_deveria_retornar_valor_do_atributo(self):
        self.assertEqual(
            listview.ListView.show_numbers,
            listview.ListView().get_show_numbers()
        )

    def test_number_display_deveria_retornar_valor_do_atributo(self):
        self.assertEqual(
            1,
            listview.ListView().number_display(1)
        )

    def test_get_breadcrumb_deveria_retornar_none(self):
        self.assertIsNone(
            listview.ListView().get_breadcrumb()
        )
