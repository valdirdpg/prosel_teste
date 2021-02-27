from django.core.management.base import BaseCommand
from django.contrib.auth import models


class Command(BaseCommand):
    help = "Modifica senha de todos os usuários"

    def handle(self, *args, **options):
        user = models.User()
        user.set_password("123")
        print(
            self.style.SQL_COLTYPE(
                '{} passwords changed to "123"'.format(
                    models.User.objects.update(password=user.password)
                )
            )
        )
