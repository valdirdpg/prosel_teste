from django.core.management.base import BaseCommand

from psct.models.analise import FaseAnalise, Modalidade, ProgressoAnalise


class Command(BaseCommand):
    help = "Inicializa a tabela ProgressoAnalise para dev"

    def handle(self, *args, **options):
        for f in FaseAnalise.objects.all():
            for c in f.edital.processo_inscricao.cursos.all():
                for m in Modalidade.objects.all():
                    ProgressoAnalise.objects.create(
                        fase=f, curso=c, modalidade=m, meta=100
                    )
