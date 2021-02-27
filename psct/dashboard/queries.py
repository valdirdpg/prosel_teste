from django.apps import apps
from django.db import models
from django.db.models import Count, Min

from psct.models import InscricaoPreAnalise, SituacaoInscricao

Inscricao = apps.get_model("psct", "Inscricao")
ParecerAvaliador = apps.get_model("psct", "ParecerAvaliador")
AvaliacaoAvaliador = apps.get_model("psct", "AvaliacaoAvaliador")
AvaliacaoHomologador = apps.get_model("psct", "AvaliacaoHomologador")
FaseRecurso = apps.get_model("psct", "FaseRecurso")


class RecursoQuery:
    SEM_AVALIADORES = 1
    COM_AVALIACAO_PENDENTE = 2
    COM_AVALIACAO_NAO_CONCLUIDA = 3
    SEM_HOMOLOGADOR = 4
    AGUARDANDO_HOMOLOGADOR = 5
    HOMOLOGADO = 6
    DEFERIDO = 7
    INDEFERIDO = 8
    AVALIADORES_INCOMPLETOS = 9

    def __init__(self, edital=None, campus=None, curso=None):
        self.edital = edital
        self.campus = campus
        self.curso = curso
        self.obj = apps.get_model("psct", "Recurso")
        params = {}
        if edital:
            params["fase__edital"] = edital
        if campus:
            params["inscricao__curso__campus"] = campus
        if curso:
            params["inscricao__curso"] = curso
        self.qs = self.obj.objects.filter(**params)

    def get_fases(self):
        if self.edital:
            return self.edital.faserecurso_set.all()
        else:
            return FaseRecurso.objects.all()

    def filter_situacao(self, situacao, fase=None):
        qs = self.qs
        if fase:
            qs = qs.filter(fase=fase)
        if situacao == self.SEM_AVALIADORES:
            qs = qs.filter(mailbox_avaliadores__isnull=True)
        elif situacao == self.COM_AVALIACAO_PENDENTE:
            qs = qs.annotate(
                avaliacoes=models.Sum(
                    models.Case(
                        models.When(pareceres_avaliadores__isnull=False, then=1),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                )
            )
            qs = qs.exclude(avaliacoes=models.F("fase__quantidade_avaliadores"))
        elif situacao == self.COM_AVALIACAO_NAO_CONCLUIDA:
            qs = qs.annotate(
                avaliacoes=models.Sum(
                    models.Case(
                        models.When(
                            pareceres_avaliadores__isnull=False,
                            pareceres_avaliadores__concluido=False,
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                )
            )
            qs = qs.filter(avaliacoes__gte=1)
        elif situacao == self.SEM_HOMOLOGADOR:
            qs = qs.filter(mailbox_homologadores__isnull=True)
        elif situacao == self.AGUARDANDO_HOMOLOGADOR:
            qs = qs.annotate(
                avaliacoes=models.Sum(
                    models.Case(
                        models.When(
                            pareceres_avaliadores__isnull=False,
                            pareceres_avaliadores__concluido=True,
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                )
            )
            # return qs.filter(avaliacoes=models.F('fase__quantidade_avaliadores'),
            #                  mailbox_homologadores__isnull=False,
            #                  pareceres_homologadores__isnull=True)
        elif situacao == self.HOMOLOGADO:
            qs = qs.filter(pareceres_homologadores__isnull=False)
        elif situacao == self.DEFERIDO:
            qs = qs.filter(
                pareceres_homologadores__isnull=False,
                pareceres_homologadores__aceito=True,
            )
        elif situacao == self.INDEFERIDO:
            qs = qs.filter(
                pareceres_homologadores__isnull=False,
                pareceres_homologadores__aceito=False,
            )
        elif situacao == self.AVALIADORES_INCOMPLETOS:
            qs = qs.annotate(
                avaliadores=models.Count("mailbox_avaliadores", distinct=True)
            )
            qs = qs.exclude(avaliadores=models.F("fase__quantidade_avaliadores"))
        return qs.distinct()


def get_inscricoes_concluidas(edital=None, campus=None, curso=None):
    params = {}
    if edital:
        params["edital"] = edital
    if campus:
        params["curso__campus"] = campus
    if curso:
        params["curso"] = curso
    return Inscricao.validas.filter(**params).distinct()


def get_inscricoes_nao_concluidas(edital=None, campus=None, curso=None):
    ids = get_inscricoes_concluidas(edital=None).values_list("id", flat=True)
    params = {}
    if edital:
        params["edital"] = edital
    if campus:
        params["curso__campus"] = campus
    if curso:
        params["curso"] = curso
    return Inscricao.objects.filter(**params).exclude(id__in=ids).distinct()


def get_inscricoes_analisadas(edital=None, campus=None, curso=None):
    params = {
        "situacao__in": [
            SituacaoInscricao.DEFERIDA.name,
            SituacaoInscricao.INDEFERIDA.name,
        ]
    }
    if edital:
        params["fase__edital"] = edital
    if campus:
        params["curso__campus"] = campus
    if curso:
        params["curso"] = curso
    return InscricaoPreAnalise.objects.filter(**params).distinct()


def get_percentual_conclusao_analise(edital=None, campus=None, curso=None):
    inscricoes = get_inscricoes_concluidas(edital, campus, curso).count()
    resultado = 0
    if inscricoes > 0:
        analisadas = get_inscricoes_analisadas(edital, campus, curso).count()
        resultado = int((analisadas / inscricoes) * 100)
    return resultado


def get_inscricoes_deferidas(edital=None, campus=None, curso=None):
    params = {"situacao": SituacaoInscricao.DEFERIDA.name}
    if edital:
        params["fase__edital"] = edital
    if campus:
        params["curso__campus"] = campus
    if curso:
        params["curso"] = curso
    return InscricaoPreAnalise.objects.filter(**params).distinct()


def get_inscricoes_indeferidas(edital=None, campus=None, curso=None):
    params = {"situacao": SituacaoInscricao.INDEFERIDA.name}
    if edital:
        params["fase__edital"] = edital
    if campus:
        params["curso__campus"] = campus
    if curso:
        params["curso"] = curso
    return InscricaoPreAnalise.objects.filter(**params).distinct()


def get_inscricoes_sem_avaliadores(edital=None, campus=None, curso=None):
    params = {"situacao": SituacaoInscricao.SEM_AVALIADORES.name}
    if edital:
        params["fase__edital"] = edital
    if campus:
        params["curso__campus"] = campus
    if curso:
        params["curso"] = curso
    return InscricaoPreAnalise.objects.filter(**params).distinct()


def get_homologacoes(edital=None, campus=None, curso=None):
    params = {}
    if edital:
        params["inscricao__fase__edital"] = edital
    if campus:
        params["inscricao__curso__campus"] = campus
    if curso:
        params["inscricao__curso"] = curso
    return AvaliacaoHomologador.objects.filter(**params).distinct()


def get_inscricoes_homologadas(edital=None, campus=None, curso=None):
    params = {"avaliacoes_homologador__isnull": False}
    if edital:
        params["fase__edital"] = edital
    if campus:
        params["curso__campus"] = campus
    if curso:
        params["curso"] = curso
    return InscricaoPreAnalise.objects.filter(**params).distinct()


def get_avaliacoes_pendentes_a_mais_tempo(edital=None, campus=None, curso=None):
    params = {"concluida": "NAO"}
    if edital:
        params["inscricao__fase__edital"] = edital
    if campus:
        params["inscricao__curso__campus"] = campus
    if curso:
        params["inscricao__curso"] = curso
    return (
        AvaliacaoAvaliador.objects.filter(**params)
        .annotate(count=Count("avaliador"), data=Min("data_cadastro"))
        .values_list("avaliador__first_name", "count", "data_cadastro")
        .distinct()
        .order_by("data")[:6]
    )


def get_melhores_avaliadores(edital=None, campus=None, curso=None):
    params = {"concluida": "SIM"}
    if edital:
        params["inscricao__fase__edital"] = edital
    if campus:
        params["inscricao__curso__campus"] = campus
    if curso:
        params["inscricao__curso"] = curso
    return (
        AvaliacaoAvaliador.objects.filter(**params)
        .values_list("avaliador__first_name")
        .annotate(count=Count("avaliador_id"))
        .distinct()
        .order_by("-count")[:6]
    )


def get_recursos(edital=None):
    params = {}
    if edital:
        params["edital"] = edital
    return FaseRecurso.objects.filter(**params).order_by("id")
