from django import template

register = template.Library()


@register.simple_tag
def consulta_format(consulta, index, data):
    format = consulta.get_format_for_coluna(index)
    if format:
        return format(data)

    if data is True:
        return "Sim"
    if data is False:
        return "Não"
    if data is None:
        return "--"

    return data
