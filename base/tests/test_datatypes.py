from django.test import TestCase

from ..custom import datatypes


class BreadCrumbTestCase(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.breadcrumb = datatypes.BreadCrumb()

    def test_deveria_inicializar_atributo_items_vazio(self):
        self.assertEqual([], self.breadcrumb.items)

    def test_add_deveria_adicionar_novo_objeto_ao_items(self):
        self.breadcrumb.add(name="test", url="test-url")
        self.assertEqual(("test", "test-url"), self.breadcrumb.items[0])

    def test_add_many_deveria_adicionar_novos_objetos_ao_items(self):
        self.breadcrumb.add_many((("test", "test-url"), ("test2", "test-url2")))
        self.assertEqual(("test", "test-url"), self.breadcrumb.items[0])
        self.assertEqual(("test2", "test-url2"), self.breadcrumb.items[1])

    def test_lancar_stop_iteration_se_breadcrumb_nao_tem_items(self):
        with self.assertRaises(StopIteration):
            next(iter(self.breadcrumb))

    def test_deveria_conseguir_iterar_sobre_os_itens(self):
        self.breadcrumb.add(name="test", url="test-url")
        self.assertEqual(("test", "test-url"), next(iter(self.breadcrumb)))

    def test_create_deveria_criar_o_objeto_e_adicionar_os_items(self):
        breadcrumb = datatypes.BreadCrumb.create(
            ("test", "test-url")
        )
        self.assertEqual(("test", "test-url"), breadcrumb.items[0])
