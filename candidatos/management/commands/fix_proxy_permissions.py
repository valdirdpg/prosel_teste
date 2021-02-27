from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Cria as permissões do proxy Candidato da app candidatos"

    def handle(self, *args, **options):
        content_type = ContentType.objects.get(
            model="candidato", app_label="candidatos"
        )
        Permission.objects.create(
            codename="add_candidato",
            name="Can add Candidato",
            content_type=content_type,
        )
        Permission.objects.create(
            codename="change_candidato",
            name="Can change Candidato",
            content_type=content_type,
        )
        Permission.objects.create(
            codename="delete_candidato",
            name="Can delete Candidato",
            content_type=content_type,
        )
