from importlib import import_module
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings, RequestFactory, TestCase
from django.urls import reverse

from . import recipes
from ..middleware import usersession


class UserSessionMiddlewareTestCase(TestCase):

    def setUp(self) -> None:
        super().setUp()

        request_factory = RequestFactory()
        self.request = request_factory.get(reverse("base"))
        self.request.user = recipes.user.make()

        engine = import_module(settings.SESSION_ENGINE)
        self.SessionStore = engine.SessionStore
        session_key = self.request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        self.request.session = self.SessionStore(session_key)

        get_response = mock.Mock()
        self.middleware = usersession.UserSessionMiddleware(get_response)

    def test_init_set_get_response_as_instance_attribute(self):
        self.assertTrue(hasattr(self.middleware, "get_response"))

    def test_deveria_expirar_sessao_para_usuario_logado(self):
        self.middleware(self.request)
        self.assertEqual(settings.SESSION_COOKIE_AGE_PSCT, self.request.session.get_expiry_age())

    def test_nao_deveria_expirar_sessao_para_usuario_logado_membro_da_equipe(self):
        self.request.user.is_staff = True
        self.middleware(self.request)
        self.assertEqual(settings.SESSION_COOKIE_AGE, self.request.session.get_expiry_age())

    @override_settings(DEBUG=True)
    def test_nao_deveria_expirar_sessao_em_modo_debug(self):
        self.middleware(self.request)
        self.assertEqual(settings.SESSION_COOKIE_AGE, self.request.session.get_expiry_age())

    def test_nao_deveria_expirar_sessao_para_usuario_nao_logado(self):
        self.request.user = AnonymousUser()
        self.middleware(self.request)
        self.assertEqual(settings.SESSION_COOKIE_AGE, self.request.session.get_expiry_age())
