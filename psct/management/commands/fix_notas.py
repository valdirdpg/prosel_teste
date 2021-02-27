from decimal import getcontext, ROUND_HALF_UP

from django.core.management.base import BaseCommand
from django.db import transaction

from psct import models


def exist_indeferimento(inscricao: models.InscricaoPreAnalise):
    avaliacao_homologador = inscricao.avaliacoes_homologador.first()
    if avaliacao_homologador:
        return True if avaliacao_homologador.texto_indeferimento else False
    avaliacoes_avaliador = inscricao.avaliacoes_avaliador.all()
    return all(bool(a.texto_indeferimento) for a in avaliacoes_avaliador)


def copy_to_preanalise(
    source: models.PontuacaoInscricao, target: models.InscricaoPreAnalise
):
    assert hasattr(target, "pontuacao")
    target.pontuacao = source.valor
    assert hasattr(target, "pontuacao_mt")
    target.pontuacao_mt = source.valor_mt
    assert hasattr(target, "pontuacao_pt")
    target.pontuacao_pt = source.valor_pt
    target.save()


class Command(BaseCommand):
    def handle(self, *args, **options):
        getcontext().rounding = ROUND_HALF_UP
        with transaction.atomic():
            for (
                resultado_inscricao
            ) in models.ResultadoPreliminarInscricao.objects.all():
                pontuacao_informada = resultado_inscricao.inscricao.pontuacao
                if pontuacao_informada.valor != round(
                    pontuacao_informada.get_pontuacao_total(), 1
                ):
                    resultado_inscricao.inscricao.pontuacao.update_pontuacao()
                    pre = resultado_inscricao.inscricao_preanalise
                    if pre.pontuacoes_homologadores.exists() and exist_indeferimento(
                        pre
                    ):
                        #  a inscrição era inicialmente indeferida e foi deferida durante o ajuste
                        if pre.deferida:
                            pontuacao_homologador = pre.pontuacoes_homologadores.first()
                            pontuacao_homologador.update_pontuacao()
                            pontuacao_homologador.deferir()
                    else:
                        copy_to_preanalise(pontuacao_informada, pre)
