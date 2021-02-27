from unittest import mock

from django.test import TestCase

from base.custom import widget


class ItemTestCase(TestCase):
    def test_deveria_ter_metodo_render(self):
        self.assertTrue(hasattr(widget.Item, "render"))

    def test_metodo_render_nao_deveria_ser_implementado(self):
        class ConcreteClass(widget.Item):
            def render(self):
                super().render()

        with self.assertRaises(NotImplementedError):
            ConcreteClass().render()


class MenuItemTestCase(TestCase):
    def test_init_deveria_criar_atributos_name_e_url(self):
        menu_item = widget.MenuItem(name="name", url="url")
        self.assertEqual("name", menu_item.name)
        self.assertEqual("url", menu_item.url)

    def test_render_deveria_retornar_html(self):
        html = '<li><a href="url">name</a></li>'
        menu_item = widget.MenuItem(name="name", url="url")
        self.assertEqual(html, menu_item.render())

    def test_repr_deveria_conter_nome_da_instancia(self):
        menu_item = widget.MenuItem(name="name", url="url")
        self.assertEqual("MenuItem (name=name, url=url)", repr(menu_item))


class SeparatorTestCase(TestCase):
    def test_render_deveria_retornar_html(self):
        html = '<li role="separator" class="divider"></li>'
        separator = widget.Separator()
        self.assertEqual(html, separator.render())


class HeaderTestCase(TestCase):
    def test_init_deveria_criar_atributos_name(self):
        header = widget.Header(name="name")
        self.assertEqual("name", header.name)

    def test_render_deveria_retornar_html(self):
        html = '<li class="dropdown-header">name</li>'
        header = widget.Header(name="name")
        self.assertEqual(html, header.render())

    def test_repr_deveria_conter_nome_da_instancia(self):
        header = widget.Header(name="name")
        self.assertEqual("Header (name=name)", repr(header))


class DisabledTestCase(TestCase):
    def test_init_deveria_criar_atributos_name(self):
        disabled = widget.Disabled(name="name")
        self.assertEqual("name", disabled.name)

    def test_render_deveria_retornar_html(self):
        html = '<li class="disabled"><a href="#">name</a></li>'
        disabled = widget.Disabled(name="name")
        self.assertEqual(html, disabled.render())

    def test_repr_deveria_conter_nome_da_instancia(self):
        disabled = widget.Disabled(name="name")
        self.assertEqual("Disabled (name=name)", repr(disabled))


class SideBarMenuTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.menu = widget.SideBarMenu
        self.menu.counter_id = 0

    def test_template_name_deveria_estar_configurado(self):
        self.assertEqual("base/dropdown_menu.html", widget.SideBarMenu.template_name)

    def test_counter_id_deveria_estar_configurado(self):
        self.assertEqual(0, widget.SideBarMenu.counter_id)

    def test_template_name_deveria_ser_sobrescrito_no_init(self):
        menu = widget.SideBarMenu(name="Name", template_name="other/template.html")
        self.assertEqual("other/template.html", menu.template_name)

    def test_init_deveria_incrementar_id_a_partir_do_counter_id(self):
        menu = widget.SideBarMenu(name="Name")
        self.assertEqual(1, menu.id)

    def test_init_deveria_usar_kwargs_como_extra_context(self):
        menu = widget.SideBarMenu("Name", extra="value")
        self.assertDictEqual({"extra": "value"}, menu.extra_context)

    def test_increment_counter_deveria_incrementar_o_counter_id(self):
        menu = widget.SideBarMenu
        menu.increment_counter()
        self.assertEqual(1, menu.counter_id)

    def test_get_new_id_deveria_incrementar_o_counter_id(self):
        menu = widget.SideBarMenu
        self.assertEqual(1, menu.get_new_id())

    @mock.patch("base.custom.widget.render_to_string")
    @mock.patch("base.custom.widget.mark_safe")
    def test_render_deveria_retornar_html(self, mark_safe, render_to_string):
        request = mock.Mock()
        menu = self.menu("Name")
        menu.render(request)
        render_to_string.assert_called_with(
            'base/dropdown_menu.html',
            context={"menu": menu},
            request=request
        )

    @mock.patch("base.custom.widget.render_to_string")
    @mock.patch("base.custom.widget.mark_safe")
    def test_render_deveria_incluir_extra_context_no_template(self, mark_safe, render_to_string):
        request = mock.Mock()
        menu = self.menu("Name", extra="value")
        menu.render(request)
        render_to_string.assert_called_with(
            'base/dropdown_menu.html',
            context={"menu": menu, "extra": "value"},
            request=request
        )

    def test_add_many_deveria_construir_menu_items_e_adicionar_ao_items(self):
        menu = self.menu("Name")
        menu.add_many(
            *[("name", "url")]
        )
        self.assertListEqual([widget.MenuItem("name", "url")], menu.items)

    def test_add_deveria_criar_menu_item_e_adicionar_ao_items(self):
        menu = self.menu("Name")
        menu.add("name", "url")
        self.assertListEqual([widget.MenuItem("name", "url")], menu.items)

    def test_add_separator_deveria_criar_separator_e_adicionar_ao_items(self):
        menu = self.menu("Name")
        menu.add_separator()
        self.assertListEqual([widget.Separator()], menu.items)

    def test_add_header_deveria_criar_header_e_adicionar_ao_items(self):
        menu = self.menu("Name")
        menu.add_header("Name")
        self.assertListEqual([widget.Header("Name")], menu.items)

    def test_add_disabled_deveria_criar_disabled_e_adicionar_ao_items(self):
        menu = self.menu("Name")
        menu.add_disabled("Name")
        self.assertListEqual([widget.Disabled("Name")], menu.items)

    def test_empty_deveria_ser_verdadeiro_se_nao_ha_itens_no_menu(self):
        self.assertTrue(self.menu("Nome").empty)

    def test_empty_deveria_ser_falso_se_ha_itens_no_menu(self):
        menu = self.menu("Name")
        menu.add_separator()
        self.assertFalse(menu.empty)
