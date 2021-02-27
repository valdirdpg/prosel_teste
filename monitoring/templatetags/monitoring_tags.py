from django import template
from django.utils.safestring import mark_safe
from monitoring import models

register = template.Library()


@register.filter(is_safe=True)
def format_state(state):
    if state == models.StateChoice.PENDING.name:
        span = '<span class="status status-pendente">Pendente</span>'
    elif state == models.StateChoice.SUCCESS.name:
        span = '<span class="status status-success">Sucesso</span>'
    elif state == models.StateChoice.FAILURE.name:
        span = '<span class="status status-error">Falha</span>'
    else:
        span = "-"
    return mark_safe(span)
