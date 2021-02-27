from django import template

from psct.models import inscricao as models

register = template.Library()


@register.simple_tag
def get_notas_por_ano(inscricao, ano):
    try:
        return inscricao.pontuacao.notas.get(ano=ano)
    except models.NotaAnual.DoesNotExist:
        return None


@register.filter
def erro_notas(dict_errors):
    erro1 = "Este campo é obrigatório."
    msg1 = "Todas as notas devem ser preenchidas."
    list_errors = []
    for dict in dict_errors:
        for error in dict.values():
            if erro1 in error and msg1 not in list_errors:
                list_errors.append(msg1)
            elif error not in list_errors:
                list_errors.append(error)
    return list_errors


@register.filter
def exists(errors):
    return any(errors)


@register.simple_tag
def title_dados_vagas(inscricao):
    if inscricao.edital.processo_inscricao.possui_segunda_opcao:
        if inscricao.curso_segunda_opcao:
            return "Dados da vaga (1ª opção)"
        else:
            return "Dados da vaga (opção única *)"
    else:
        return "Dados da vaga"


@register.simple_tag
def modalidade_por_nivel_formacao(modalidade, processo_inscricao):
    return modalidade.por_nivel_formacao(processo_inscricao)
