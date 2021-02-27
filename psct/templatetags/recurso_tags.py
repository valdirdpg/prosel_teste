from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def servidor_display(dictionary, username):
    return "{} ({}) - {}".format(
        dictionary[username]["nome"],
        dictionary[username]["matricula"],
        dictionary[username]["campus"],
    )


@register.simple_tag
def pode_substituir_avaliador(recurso, avaliador):
    return not recurso.pareceres_avaliadores.filter(avaliador=avaliador).exists()


@register.simple_tag
def pode_substituir_homologador(recurso, homologador):
    return not recurso.pareceres_homologadores.filter(homologador=homologador).exists()


@register.filter
def aceito_format(status):
    if status:
        return mark_safe('<span class="status status-info">Sim</span>')
    return mark_safe('<span class="status status-pendente">Não</span>')
