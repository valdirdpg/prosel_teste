from django import template

from candidatos import utils

register = template.Library()


@register.simple_tag
def exibe_prematricula(user):
    return utils.is_candidato_prematricula(user)
