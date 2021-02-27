import base.tests.recipes


class UserTestMixin:

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.usuario_base = base.tests.recipes.user.make()
        cls.usuario_base.set_password("123")
        cls.usuario_base.save()
        cls.usuario_base.credentials = {
            "username": cls.usuario_base.username,
            "password": "123",
        }
