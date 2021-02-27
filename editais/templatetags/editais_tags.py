from django import template

from editais import models

register = template.Library()


@register.simple_tag
def has_anexo(edital):
    return models.Documento.objects.filter(edital=edital, categoria="ANEXO").exists()


@register.simple_tag
def data_interesse_em_etapa(etapa):
    if models.PeriodoConvocacao.objects.filter(
        etapa=etapa, evento="INTERESSE"
    ).exists():
        return models.PeriodoConvocacao.objects.filter(
            etapa=etapa, evento="INTERESSE"
        ).first()
    else:
        return None
