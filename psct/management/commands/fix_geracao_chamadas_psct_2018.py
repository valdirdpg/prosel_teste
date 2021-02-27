from django.core.management.base import BaseCommand

from cursos import models as c_models
from processoseletivo import models as p_models
from psct import models


def apagar_etapas_chamadas(resultado):
    edicao = resultado.fase.edital.edicao
    print(f"Apagando chamadas de {edicao}:")
    print(
        "{} chamada(s) apagada(s).".format(
            p_models.Chamada.objects.filter(etapa__edicao=edicao).delete()[0]
        )
    )
    print(f"Apagando etapas de {edicao}:")
    print(
        "{} etapa(s) apagada(s).".format(
            p_models.Etapa.objects.filter(edicao=edicao).delete()[0]
        )
    )


def gerar_etapas_chamadas(resultado):
    edicao = resultado.fase.edital.edicao

    for campus in c_models.Campus.objects.filter(
        cursonocampus__resultadopreliminarcurso__resultado=resultado
    ).distinct():
        etapa, created = p_models.Etapa.objects.update_or_create(
            edicao=edicao, campus=campus, numero=0, defaults=dict(multiplicador=1)
        )

        if not created:
            p_models.Chamada.objects.filter(etapa=etapa).delete()

        etapa.gerar_chamadas()
    print(f"Novas etapas e chamadas foram criadas para {edicao}.")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("resultado", nargs="+", type=int)

    def handle(self, *args, **options):

        for resultado_pk in options["resultado"]:
            resultado = models.ResultadoPreliminar.objects.get(pk=resultado_pk)
            apagar_etapas_chamadas(resultado)
            gerar_etapas_chamadas(resultado)
