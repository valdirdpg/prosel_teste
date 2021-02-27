from django.core.management.base import BaseCommand

from ifpb_django_permissions.perms import sync


class Command(BaseCommand):
    help = "Sincroniza as permissões da aplicação"

    def handle(self, *args, **options):
        sync()
