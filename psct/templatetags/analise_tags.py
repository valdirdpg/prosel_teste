from django import template
from django.utils.safestring import mark_safe

from psct.models import analise as models

register = template.Library()


@register.filter
def situacao_format(situacao):
    if situacao == models.SituacaoAvaliacao.DEFERIDA.value:
        css = "deferido"
    else:
        css = "indeferido"
    return mark_safe(f'<span class="status status-{css}">{situacao}</span>')


@register.filter
def concluida_format(concluida):
    if concluida == models.Concluida.SIM.value:
        css = "sim"
    else:
        css = "nao"
    return mark_safe(f'<span class="status status-{css}">{concluida}</span>')
