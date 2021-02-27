from django.core.management.base import BaseCommand

from processoseletivo.models import Modalidade as ModalidadePadrao
from psct.models import Modalidade


class Command(BaseCommand):
    help = "Importa as modalidades do processo seletivo para edição"

    def handle(self, *args, **options):
        for modalidade in ModalidadePadrao.objects.all():
            Modalidade.objects.create(equivalente=modalidade, texto="")
