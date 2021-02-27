from django import template

register = template.Library()


@register.filter
def total_inscritos(curso, processo_inscricao):
    queryset = curso.inscricao_set.filter(
        cancelamento__isnull=True, aceite=True, comprovantes__isnull=False
    )
    if processo_inscricao:
        return (
            queryset.filter(edital__processo_inscricao=processo_inscricao)
            .distinct()
            .count()
        )
    else:
        return queryset.distinct().count()
