import random

from django.conf import settings
from django.core.management.base import BaseCommand

from psct.models import (
    Candidato, Comprovante, Inscricao, ModalidadeVagaCursoEdital, PontuacaoInscricao,
    ProcessoInscricao,
)


class Command(BaseCommand):
    help = "Inscreve candidatos no PSCT"

    def add_arguments(self, parser):
        parser.add_argument("processo_inscricao", nargs="+", type=int)

    def handle(self, *args, **options):
        if not settings.DEBUG:
            print("Comando não permitido!")
        else:
            processo_inscricao = None
            processo_inscricao_id = options["processo_inscricao"][0]
            if processo_inscricao_id:
                processo_inscricao = ProcessoInscricao.objects.filter(
                    pk=processo_inscricao_id
                ).first()
            if processo_inscricao is None:
                print("Processo informado não existe.")
                return

            edital = processo_inscricao.edital
            candidatos = Candidato.objects.all()

            quantidade = 20
            for m in ModalidadeVagaCursoEdital.objects.filter(
                curso_edital__edital=edital, quantidade_vagas__gt=0
            ):
                curso = m.curso_edital.curso
                modalidade = m.modalidade
                for candidato in candidatos[:quantidade]:
                    inscricao = Inscricao.objects.create(
                        candidato=candidato,
                        edital=edital,
                        curso=curso,
                        modalidade_cota=modalidade,
                        aceite=True,
                    )
                    pontuacao = PontuacaoInscricao.objects.get(inscricao=inscricao)
                    pontuacao.ensino_regular = False
                    pontuacao.save()
                    pontuacao.criar_notas()
                    for nota in pontuacao.notas.all():
                        nota.portugues = round(random.uniform(7, 10), 1)
                        nota.matematica = round(random.uniform(7, 10), 1)
                        nota.historia = round(random.uniform(7, 10), 1)
                        nota.geografia = round(random.uniform(7, 10), 1)
                        nota.save()
                    pontuacao.update_pontuacao()

                    comprovante = Comprovante()
                    comprovante.arquivo.name = "/"
                    comprovante.nome = "Notas do Enem"
                    comprovante.inscricao = inscricao
                    comprovante.save()
                candidatos = candidatos[quantidade:]

            print(
                "{} candidatos inscritos.".format(
                    ModalidadeVagaCursoEdital.objects.filter(
                        curso_edital__edital=edital, quantidade_vagas__gt=0
                    ).count()
                    * quantidade
                )
            )
