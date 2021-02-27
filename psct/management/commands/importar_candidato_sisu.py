from django.core.management.base import BaseCommand

from psct.models import importar_candidato_sisu


class Command(BaseCommand):
    help = "Importar candidatos SISU no PSCT"

    def add_arguments(self, parser):
        parser.add_argument("cpfs", nargs="+", type=str)

    def handle(self, *args, **options):
        for cpf in options["cpfs"]:
            importar_candidato_sisu(cpf)
