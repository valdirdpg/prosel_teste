import datetime

from django.test import TestCase
from django.urls import reverse

from base.tests.mixins import UserTestMixin
from psct.tests import mixins
from .. import permissions


class ProcessoInscricaoAdminTestCase(UserTestMixin, mixins.EditalTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.AdministradoresPSCT().sync()
        permissions.AdministradoresPSCT.add_user(cls.usuario_base)
        cls.usuario_base.is_staff = True
        cls.usuario_base.save()

    def setUp(self):
        super().setUp()
        self.client.login(**self.usuario_base.credentials)

    def test_administrador_deveria_conseguir_realizar_cadastro_basico(self):
        date_today = datetime.date.today()
        response = self.client.post(
            reverse("admin:psct_processoinscricao_add"),
            data=dict(
                edital=self.edital.pk,
                formacao="SUBSEQUENTE",
                data_inicio=date_today,
                data_encerramento=date_today,
            ),
        )
        self.assertEqual(response.status_code, 200)
