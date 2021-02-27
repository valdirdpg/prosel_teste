from django import template
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from processoseletivo import models

register = template.Library()


@register.simple_tag
def vagas_por_curso_na_etapa(etapa, curso):
    chamadas = models.Chamada.objects.filter(etapa=etapa, curso=curso)
    if chamadas:
        return chamadas.aggregate(Sum("vagas")).get("vagas__sum")
    else:
        return 0


@register.simple_tag
def vagas_disponiveis(processo_seletivo, campus):
    return campus.vagas(processo_seletivo)


@register.simple_tag
def vagas_por_campus(etapa, campus):
    chamadas = models.Chamada.objects.filter(etapa=etapa, curso__campus=campus)
    if chamadas:
        return chamadas.aggregate(Sum("vagas")).get("vagas__sum")
    else:
        return 0


@register.simple_tag
def get_convocacoes_abertas(user):
    return (
        models.Inscricao.objects.filter(
            candidato__pessoa__user=user,
            chamada__etapa__publica=True,
            chamada__etapa__encerrada=False,
        )
        .order_by("chamada__etapa")
        .distinct()
    )


@register.simple_tag
def vagas_por_curso_na_modalidade(etapa, curso, modalidade):
    return models.Chamada.objects.get(
        etapa=etapa, curso=curso, modalidade=modalidade
    ).vagas


@register.simple_tag
def matriculado_em_chamada(inscricao, etapa):
    return inscricao.get_matriculado_em_chamada(etapa)


@register.simple_tag
def situacao_matricula_em_chamada(inscricao, etapa):
    return inscricao.get_situacao_matricula_em_chamada(etapa)


@register.simple_tag
def get_situacao_matricula_outra_chamada(inscricao, etapa):
    return inscricao.get_situacao_matricula_outra_chamada(etapa)


@register.simple_tag
def confirmou_interesse_em_chamada(inscricao, etapa):
    return models.ConfirmacaoInteresse.objects.filter(
        inscricao=inscricao, etapa=etapa
    ).exists()


@register.simple_tag
def status_documentacao(inscricao):
    return inscricao.status_documentacao()


@register.simple_tag
def status_recurso(inscricao):
    return inscricao.status_recurso()


@register.simple_tag
def has_etapa_aberta():
    return models.Etapa.objects.filter(encerrada=False).exists()


@register.simple_tag
def get_edital(edicao):
    return edicao.edital_set.filter(tipo="ABERTURA").first()


@register.filter
def get_modalidade_ensino_fundamental(modalidade):
    return modalidade.replace("ensino médio", "ensino fundamental")


@register.simple_tag
def ondeestou(request):
        localizacao = {}
        localizacao['onde_estou'] = "PCD"
            
        return render(request,'processoseletivo/portal/pcd.html',localizacao)
