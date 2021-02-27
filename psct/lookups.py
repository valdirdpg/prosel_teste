import operator
from functools import reduce

from ajax_select import LookupChannel, register
from django.db.models import Q

from psct.models.recurso import GrupoEdital


@register("grupos")
class GrupoLookup(LookupChannel):
    model = GrupoEdital

    def _construct_query(self, q):
        return reduce(
            operator.and_, [Q(grupo__name__unaccent__icontains=p) for p in q.split()]
        )

    def get_query(self, q, request):
        return self.model.objects.filter(self._construct_query(q)).distinct()[:10]
