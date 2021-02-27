from unittest import mock

from django.contrib.auth.models import Group, User
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.test import TestCase
from model_mommy import mommy

from cursos.models import Campus
from ..custom.views import mixin


class GroupRequiredMixinTestCase(TestCase):
    def test_deveria_ter_atributo_de_classe_group_required(self):
        self.assertTrue(hasattr(mixin.GroupRequiredMixin, "group_required"))

    def test_get_group_required_deveria_lancar_excecao_se_group_required_for_none(self):
        with self.assertRaises(ImproperlyConfigured):
            mixin.GroupRequiredMixin().get_group_required()

    def test_get_group_required_deveria_retornar_lista(self):
        group_required_mixin = mixin.GroupRequiredMixin()
        group_required_mixin.group_required = "Group name"
        self.assertIsInstance(group_required_mixin.get_group_required(), tuple)

    def test_get_group_required_deveria_retornar_str_como_item_na_lista(self):
        group_required_mixin = mixin.GroupRequiredMixin()
        group_required_mixin.group_required = "Group name"
        self.assertTupleEqual(("Group name",), group_required_mixin.get_group_required())

    def test_get_group_required_deveria_retornar_todos_os_grupos_definidos(self):
        group_required_mixin = mixin.GroupRequiredMixin()
        group_required_mixin.group_required = ("Group name", "Other group")
        self.assertTupleEqual(
            ("Group name", "Other group"),
            group_required_mixin.get_group_required()
        )

    def test_has_permission_deveria_retornar_verdadeiro_se_user_estiver_no_grupo(self):
        user = mommy.make(User)
        group = mommy.make(Group)
        user.groups.add(group)
        group_required_mixin = mixin.GroupRequiredMixin()
        group_required_mixin.request = mock.Mock()
        group_required_mixin.request.user = user
        group_required_mixin.group_required = group.name
        self.assertTrue(group_required_mixin.has_permission())

    def test_has_permission_deveria_retornar_verdadeiro_para_superuser(self):
        user = mommy.make(User, is_superuser=True)
        group_required_mixin = mixin.GroupRequiredMixin()
        group_required_mixin.group_required = "Group name"
        group_required_mixin.request = mock.Mock()
        group_required_mixin.request.user = user
        self.assertTrue(group_required_mixin.has_permission())

    @mock.patch("base.custom.views.mixin.GroupRequiredMixin.has_permission")
    def test_dispatch_deveria_lancar_permission_denied_se_user_nao_tem_permissao(
            self,
            has_permission
    ):
        has_permission.return_value = False
        group_required_mixin = mixin.GroupRequiredMixin()
        group_required_mixin.group_required = "Group name"
        group_required_mixin.raise_exception = True
        with self.assertRaises(PermissionDenied):
            group_required_mixin.dispatch(mock.Mock())


class AnyGroupRequiredMixinTestCase(TestCase):
    def test_has_permission_deveria_retornar_verdadeiro_se_user_estiver_no_grupo(self):
        user = mommy.make(User)
        group = mommy.make(Group)
        user.groups.add(group)
        group_required_mixin = mixin.AnyGroupRequiredMixin()
        group_required_mixin.request = mock.Mock()
        group_required_mixin.request.user = user
        group_required_mixin.group_required = group.name
        self.assertTrue(group_required_mixin.has_permission())

    def test_has_permission_deveria_retornar_verdadeiro_para_superuser(self):
        user = mommy.make(User, is_superuser=True)
        group_required_mixin = mixin.AnyGroupRequiredMixin()
        group_required_mixin.group_required = "Group name"
        group_required_mixin.request = mock.Mock()
        group_required_mixin.request.user = user
        self.assertTrue(group_required_mixin.has_permission())


class UserPermissionsListMixinTestCase(TestCase):
    def test_list_display_deveria_ter_colunas_padrao(self):
        self.assertListEqual(
            ["usuario", "campi", "permissoes", "acoes"],
            mixin.UserPermissionsListMixin.list_display
        )

    def test_model_deveria_ter_user(self):
        self.assertEqual(User, mixin.UserPermissionsListMixin.model)

    def test_ordering_deveria_ter_colunas_padrao(self):
        self.assertListEqual(
            ["first_name", "last_name", "username"],
            mixin.UserPermissionsListMixin.ordering
        )

    def test_template_name_deveria_ter_valor_padrao(self):
        self.assertEqual("reuse/listview.html", mixin.UserPermissionsListMixin.template_name)

    def test_campi_deveria_ter_valor_padrao(self):
        obj = mock.Mock()
        obj.lotacoes.all.return_value.exists.return_value = False
        self.assertEqual("-", mixin.UserPermissionsListMixin().campi(obj))

    @mock.patch("cursos.models.Campus.cria_usuarios_diretores")
    @mock.patch("cursos.models.Campus.adiciona_permissao_diretores")
    @mock.patch("cursos.models.Campus.remove_permissao_diretores")
    def test_campi_com_lotacao_deveria_retornar_lista_html(self, remove, adiciona, cria):
        user = mommy.make(User)
        campus = mommy.make(Campus)
        campus.servidores.add(user)
        self.assertEqual(
            f"<ul><li>{campus}</li></ul>",
            mixin.UserPermissionsListMixin().campi(user)
        )

    def test_usuario_deveria_exibir_nome_e_username(self):
        user = mommy.make(User)
        self.assertEqual(
            f"{user.get_full_name()} ({user.username})",
            mixin.UserPermissionsListMixin().usuario(user)
        )

    @mock.patch("base.custom.views.mixin.UserPermissionsListMixin.get_grupos_gerenciados")
    def test_permissoes_deveria_exibir_vazio_se_user_nao_estah_em_um_dos_grupos_gerenciados(
            self, get
    ):
        get.return_value = []
        user = mommy.make(User)
        list_mixin = mixin.UserPermissionsListMixin()
        self.assertEqual(
            "<ul></ul>",
            list_mixin.permissoes(user)
        )

    def test_permissoes_deveria_exibir_nomes_dos_grupos_gerenciados(self):
        user = mommy.make(User)
        group = mommy.make(Group)
        user.groups.add(group)
        list_mixin = mixin.UserPermissionsListMixin()
        list_mixin.grupos_gerenciados = [group.name]
        self.assertEqual(
            f"<ul><li>{group}</li></ul>",
            list_mixin.permissoes(user)
        )

    def test_get_breadcrumb_deveria_retornar_titulo(self):
        list_mixin = mixin.UserPermissionsListMixin()
        list_mixin.get_title = lambda: "Title"
        self.assertEqual((("Title", ""),), list_mixin.get_breadcrumb())

    def test_get_grupos_gerenciados_deveria_retornar_valor_atributo_de_classe(self):
        list_mixin = mixin.UserPermissionsListMixin()
        list_mixin.grupos_gerenciados = "Group"
        self.assertEqual("Group", list_mixin.get_grupos_gerenciados())
