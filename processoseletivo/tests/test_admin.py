from django.test import TestCase
from django.urls import reverse

import base.permissions
import editais.permissions
from base.tests.mixins import UserTestMixin
from . import recipes


class ProcessoSeletivoAdminAdministradoresSistemicosTestCase(UserTestMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        base.permissions.AdministradoresSistemicos().sync()
        cls.usuario_base.is_staff = True
        cls.usuario_base.save()
        base.permissions.AdministradoresSistemicos.add_user(cls.usuario_base)

    def setUp(self) -> None:
        super().setUp()
        self.client.login(**self.usuario_base.credentials)

    def test_deveria_conseguir_listar_processos_seletivos(self):
        response = self.client.get(reverse("admin:processoseletivo_processoseletivo_changelist"))
        self.assertEqual(200, response.status_code)

    def test_deveria_conseguir_adicionar_processos_seletivos(self):
        response = self.client.get(reverse("admin:processoseletivo_processoseletivo_add"))
        self.assertEqual(200, response.status_code)

    def test_deveria_conseguir_alterar_processos_seletivos(self):
        processo = recipes.processo_seletivo.make()
        response = self.client.get(
            reverse("admin:processoseletivo_processoseletivo_change", args=[processo.id])
        )
        self.assertEqual(200, response.status_code)


class ProcessoSeletivoAdminAdministradoresSistemicosdeEditaisTestCase(UserTestMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        editais.permissions.AdministradoresSistemicosdeEditais().sync()
        cls.usuario_base.is_staff = True
        cls.usuario_base.save()
        editais.permissions.AdministradoresSistemicosdeEditais.add_user(cls.usuario_base)

    def setUp(self) -> None:
        super().setUp()
        self.client.login(**self.usuario_base.credentials)

    def test_administrador_editais_deveria_conseguir_listar_processos_seletivos(self):
        response = self.client.get(reverse("admin:processoseletivo_processoseletivo_changelist"))
        self.assertEqual(200, response.status_code)

    def test_administrador_editais_deveria_conseguir_adicionar_processos_seletivos(self):
        response = self.client.get(reverse("admin:processoseletivo_processoseletivo_add"))
        self.assertEqual(200, response.status_code)

    def test_deveria_conseguir_alterar_processos_seletivos(self):
        processo = recipes.processo_seletivo.make()
        response = self.client.get(
            reverse("admin:processoseletivo_processoseletivo_change", args=[processo.id])
        )
        self.assertEqual(200, response.status_code)
