from datetime import date

from django import template
from django.template.defaultfilters import pluralize

import base.choices
from base.utils import human_list, join_by
from .. import choices

register = template.Library()


@register.filter()
def tsi(passado):
    if not passado:
        return "-"
    hoje = date.today()
    tempo = date.fromordinal(hoje.toordinal() - passado.toordinal())
    return f"{tempo.year} ano{pluralize(tempo.year)}"


@register.filter()
def rt(regime):
    return "-" if not regime else choices.RegimeTrabalho.label(rt)


@register.filter()
def titulacao(titulo):
    return "-" if not titulo else base.choices.Titulacao.label(titulo)


@register.filter()
def as_human_list(lista):
    return human_list(lista)


@register.filter()
def join(value, arg):
    return join_by(value, arg)


@register.filter
def label_formacao(text):
    return choices.Formacao.label(text)
