from django import template

register = template.Library()


@register.filter
def ano_format(ano):
    if ano:
        return f"{ano} º ano"
    return "Supletivo/Enem/Outros"


@register.simple_tag
def get_avaliadores_pontuacao(inscricao):
    return [mb.avaliador for mb in inscricao.mailbox_pontuacao_avaliador.all()]


@register.simple_tag
def get_homologadores_pontuacao(inscricao):
    return [mb.homologador for mb in inscricao.mailbox_pontuacao_homologador.all()]
