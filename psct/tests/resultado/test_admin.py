from unittest import mock

from django.contrib import admin as django_admin
from django.contrib.admin import AdminSite
from django.contrib.admin import ModelAdmin
from django.test import TestCase

import cursos.models
import cursos.recipes
from psct import models
from psct.admin import resultado as admin

from .. import recipes


class ResultadoPreliminarEditalFilterTestCase(TestCase):
    def test_title_deveria_estar_corretamente_configurado(self):
        resultado_filter = admin.ResultadoPreliminarEditalFilter
        self.assertEqual("Resultado Preliminar de Edital", resultado_filter.title)

    def test_parameter_name_deveria_estar_corretamente_configurado(self):
        resultado_filter = admin.ResultadoPreliminarEditalFilter
        self.assertEqual("resultado_preliminar", resultado_filter.parameter_name)

    def test_lookups_deveria_estar_corretamente_configurado(self):
        request = model = model_admin = params = mock.MagicMock()
        resultado_filter = admin.ResultadoPreliminarEditalFilter(request, params, model, model_admin)
        self.assertEqual([(0, "Não"), (1, "Sim")], resultado_filter.lookups(request, model_admin))

    @mock.patch.object(admin.ResultadoPreliminarEditalFilter, "value")
    def test_queryset_deveria_filtrar_pelo_resultado_homologado(self, value):
        self.campus_patcher = mock.patch.multiple(
            cursos.models.Campus,
            cria_usuarios_diretores=mock.DEFAULT,
            adiciona_permissao_diretores=mock.DEFAULT,
            remove_permissao_diretores=mock.DEFAULT
        )
        self.fase_analise_patcher = mock.patch.multiple(
            models.FaseAnalise,
            atualizar_grupos_permissao=mock.DEFAULT,
        )
        self.campus_patcher.start()
        self.fase_analise_patcher.start()
        value.return_value = "1"
        resultado = recipes.resultado_preliminar.make()
        resultado_homologado = recipes.resultado_preliminar_homologado.make().resultado
        self.campus_patcher.stop()
        self.fase_analise_patcher.stop()
        request = model = model_admin = params = mock.MagicMock()
        resultado_filter = admin.ResultadoPreliminarEditalFilter(
            request, params, model, model_admin
        )
        queryset = models.ResultadoPreliminar.objects.all()
        self.assertIn(
            resultado_homologado,
            resultado_filter.queryset(request, queryset)
        )
        self.assertNotIn(
            resultado,
            resultado_filter.queryset(request, queryset)
        )

    @mock.patch.object(admin.ResultadoPreliminarEditalFilter, "value")
    def test_queryset_sem_value_nao_deveria_filtrar(self, value):
        value.return_value = ''
        request = model = model_admin = params = mock.MagicMock()
        resultado_filter = admin.ResultadoPreliminarEditalFilter(
            request, params, model, model_admin
        )
        queryset = models.ResultadoPreliminar.objects.all()
        self.assertEqual(queryset, resultado_filter.queryset(request, queryset))


class ResultadoFinalFilterTestCase(TestCase):
    def test_title_deve_esta_corretamente_configurado(self):
        self.assertEqual("Resultado de Edital", admin.ResultadoFinalFilter.title)

    def test_parameter_name_deve_esta_corretamente_configurado(self):
        self.assertEqual("resultado", admin.ResultadoFinalFilter.parameter_name)

    def test_lookups_deve_esta_corretamente_configurado(self):
        request = model = model_admin = params = mock.MagicMock()
        resultado_filter = admin.ResultadoFinalFilter(
            request, params, model, model_admin
        )
        self.assertEqual(
            [(0, "Não"), (1, "Sim")],
            resultado_filter.lookups(request, model_admin)
        )

    @mock.patch.object(admin.ResultadoFinalFilter, "value")
    def test_queryset_deveria_filtrar_pelo_resultado_homologado(self, value):
        self.campus_patcher = mock.patch.multiple(
            cursos.models.Campus,
            cria_usuarios_diretores=mock.DEFAULT,
            adiciona_permissao_diretores=mock.DEFAULT,
            remove_permissao_diretores=mock.DEFAULT
        )
        self.fase_analise_patcher = mock.patch.multiple(
            models.FaseAnalise,
            atualizar_grupos_permissao=mock.DEFAULT,
        )
        self.campus_patcher.start()
        self.fase_analise_patcher.start()
        value.return_value = "1"
        resultado = recipes.resultado_preliminar.make()
        resultado_final = recipes.resultado_final.make().resultado
        self.campus_patcher.stop()
        self.fase_analise_patcher.stop()
        request = model = model_admin = params = mock.MagicMock()
        resultado_filter = admin.ResultadoFinalFilter(
            request, params, model, model_admin
        )
        queryset = models.ResultadoPreliminar.objects.all()
        self.assertIn(
            resultado_final,
            resultado_filter.queryset(request, queryset)
        )
        self.assertNotIn(
            resultado,
            resultado_filter.queryset(request, queryset)
        )

    @mock.patch.object(admin.ResultadoFinalFilter, "value")
    def test_queryset_sem_value_nao_deveria_filtrar(self, value):
        value.return_value = ''
        request = model = model_admin = params = mock.MagicMock()
        resultado_filter = admin.ResultadoFinalFilter(
            request, params, model, model_admin
        )
        queryset = models.ResultadoPreliminar.objects.all()
        self.assertEqual(queryset, resultado_filter.queryset(request, queryset))


class ResultadoPreliminarAdminTestCase(TestCase):
    def test_list_display_deve_esta_corretamente_configurado(self):
        self.assertEqual(
            ("id", "edital_display", "data_cadastro", "acoes"),
            admin.ResultadoPreliminarAdmin.list_display
        )

    def test_list_filter_deveria_ter_fase_edital(self):
        self.assertEqual(
            "fase__edital",
            admin.ResultadoPreliminarAdmin.list_filter[0][0]
        )

    def test_list_filter_deveria_ter_resultado_preliminar_filter(self):
        self.assertIn(
            admin.ResultadoPreliminarEditalFilter,
            admin.ResultadoPreliminarAdmin.list_filter
        )

    def test_list_filter_deveria_ter_resultado_final_filter(self):
        self.assertIn(
            admin.ResultadoFinalFilter,
            admin.ResultadoPreliminarAdmin.list_filter
        )

    def test_list_display_links_deveria_esta_corretamente_configurado(self):
        self.assertIsNone(admin.ResultadoPreliminarAdmin.list_display_links)

    def test_has_change_permission_deveria_retornar_falso_para_um_objeto(self):
        resultado_admin = admin.ResultadoPreliminarAdmin(models.ResultadoPreliminar, AdminSite())
        request = mock.Mock()
        obj = mock.Mock()
        self.assertFalse(resultado_admin.has_change_permission(request, obj))

    @mock.patch.object(ModelAdmin, "has_change_permission")
    def test_has_change_permission_deveria_retornar_valor_da_permissao(self, has_change_permission):
        has_change_permission.return_value = True
        resultado_admin = admin.ResultadoPreliminarAdmin(models.ResultadoPreliminar, AdminSite())
        request = mock.Mock()
        self.assertTrue(resultado_admin.has_change_permission(request))

    def test_has_add_permission_deveria_retornar(self):
        resultado_admin = admin.ResultadoPreliminarAdmin(models.ResultadoPreliminar, AdminSite())
        request = mock.Mock()
        self.assertFalse(resultado_admin.has_add_permission(request))

    def test_edital_display_deveria_retornar_valor_formatado(self):
        resultado_admin = admin.ResultadoPreliminarAdmin(models.ResultadoPreliminar, AdminSite())
        self.campus_patcher = mock.patch.multiple(
            cursos.models.Campus,
            cria_usuarios_diretores=mock.DEFAULT,
            adiciona_permissao_diretores=mock.DEFAULT,
            remove_permissao_diretores=mock.DEFAULT
        )
        self.fase_analise_patcher = mock.patch.multiple(
            models.FaseAnalise,
            atualizar_grupos_permissao=mock.DEFAULT,
        )
        self.campus_patcher.start()
        self.fase_analise_patcher.start()
        resultado = recipes.resultado_preliminar.make()
        self.campus_patcher.stop()
        self.fase_analise_patcher.stop()

        edital = resultado.fase.edital
        self.assertEqual(
            f"{edital.numero}/{edital.ano}",
            resultado_admin.edital_display(resultado)
        )

    def test_edital_display_deveria_ter_short_description_corretamente_configurado(self):
        self.assertEqual(
            "Edital",
            admin.ResultadoPreliminarAdmin.edital_display.short_description
        )

    def test_acoes_deveria_ter_short_description_corretamente_configurado(self):
        self.assertEqual(
            "Ações",
            admin.ResultadoPreliminarAdmin.acoes.short_description
        )

    @mock.patch("psct.admin.resultado.reverse")
    @mock.patch("psct.admin.resultado.SideBarMenu")
    def test_acoes_deveria_renderizar_menu(self, menu, reverse):
        menu.return_value.render.return_value = mock.Mock()
        resultado_admin = admin.ResultadoPreliminarAdmin(models.ResultadoPreliminar, AdminSite())
        obj = mock.Mock()
        resultado_admin.acoes(obj)
        menu.return_value.render.assert_called_once()

    @mock.patch("psct.admin.resultado.reverse")
    @mock.patch("psct.admin.resultado.SideBarMenu")
    def test_acoes_deveria_ter_menu_exportar_arquivo(self, menu, reverse):
        menu.items = []
        mocked_url = mock.Mock()
        reverse.return_value = mocked_url

        def mocked_add(name, url):
            menu.items.append((name, url))

        menu.return_value.add = mocked_add

        resultado_admin = admin.ResultadoPreliminarAdmin(models.ResultadoPreliminar, AdminSite())
        obj = mock.Mock()
        resultado_admin.acoes(obj)

        self.assertEqual(
            ("Exportar para arquivo", mocked_url),
            menu.items[0]
        )

    @mock.patch("psct.admin.resultado.reverse")
    @mock.patch("psct.admin.resultado.SideBarMenu")
    def test_acoes_deveria_ter_menu_visualizar_vagas(self, menu, reverse):
        menu.items = []
        mocked_url = mock.Mock()
        reverse.return_value = mocked_url

        def mocked_add(name, url):
            menu.items.append((name, url))

        menu.return_value.add = mocked_add

        resultado_admin = admin.ResultadoPreliminarAdmin(models.ResultadoPreliminar, AdminSite())
        obj = mock.Mock()
        resultado_admin.acoes(obj)

        self.assertEqual(
            ("Visualizar vagas", mocked_url),
            menu.items[-1]
        )

    @mock.patch("psct.admin.resultado.reverse")
    @mock.patch("psct.admin.resultado.SideBarMenu")
    def test_acoes_deveria_ter_menu_definir_resultado_preliminar(self, menu, reverse):
        menu.items = []
        mocked_url = mock.Mock()
        reverse.return_value = mocked_url

        def mocked_add(name, url):
            menu.items.append((name, url))

        menu.return_value.add = mocked_add

        resultado_admin = admin.ResultadoPreliminarAdmin(models.ResultadoPreliminar, AdminSite())
        obj = mock.Mock()
        delattr(obj.fase.edital, "resultado_preliminar")
        resultado_admin.acoes(obj)

        self.assertEqual(
            ("Definir como resultado preliminar do edital", mocked_url),
            menu.items[1]
        )

    @mock.patch("psct.admin.resultado.reverse")
    @mock.patch("psct.admin.resultado.SideBarMenu")
    def test_acoes_deveria_ter_menu_remover_resultado_preliminar(self, menu, reverse):
        menu.items = []
        mocked_url = mock.Mock()
        reverse.return_value = mocked_url

        def mocked_add(name, url):
            menu.items.append((name, url))

        menu.return_value.add = mocked_add

        resultado_admin = admin.ResultadoPreliminarAdmin(models.ResultadoPreliminar, AdminSite())
        obj = mock.Mock()
        obj.fase.edital.resultado_preliminar.resultado = obj
        delattr(obj.fase.edital, "resultado")
        resultado_admin.acoes(obj)

        self.assertEqual(
            ("Remover resultado preliminar do edital", mocked_url),
            menu.items[1]
        )

    @mock.patch("psct.admin.resultado.reverse")
    @mock.patch("psct.admin.resultado.SideBarMenu")
    def test_acoes_deveria_ter_menu_definir_resultado_final(self, menu, reverse):
        menu.items = []
        mocked_url = mock.Mock()
        reverse.return_value = mocked_url

        def mocked_add(name, url):
            menu.items.append((name, url))

        menu.return_value.add = mocked_add

        resultado_admin = admin.ResultadoPreliminarAdmin(models.ResultadoPreliminar, AdminSite())
        obj = mock.Mock()
        delattr(obj.fase.edital, "resultado")
        resultado_admin.acoes(obj)

        self.assertEqual(
            ("Definir como resultado final do edital", mocked_url),
            menu.items[1]
        )

    @mock.patch("psct.admin.resultado.reverse")
    @mock.patch("psct.admin.resultado.SideBarMenu")
    def test_acoes_deveria_ter_menu_remover_resultado_final(self, menu, reverse):
        menu.items = []
        mocked_url = mock.Mock()
        reverse.return_value = mocked_url

        def mocked_add(name, url):
            menu.items.append((name, url))

        menu.return_value.add = mocked_add

        resultado_admin = admin.ResultadoPreliminarAdmin(models.ResultadoPreliminar, AdminSite())
        obj = mock.Mock()
        obj.fase.edital.resultado.resultado = obj
        resultado_admin.acoes(obj)

        self.assertEqual(
            ("Remover resultado de edital", mocked_url),
            menu.items[1]
        )

    def test_registered(self):
        self.assertTrue(
            django_admin.site.is_registered(models.ResultadoPreliminar)
        )
        self.assertIsInstance(
            django_admin.site._registry[models.ResultadoPreliminar], admin.ResultadoPreliminarAdmin
        )
