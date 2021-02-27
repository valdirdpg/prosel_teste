import operator
from functools import reduce

from ajax_select import LookupChannel, register
from django.db.models import Q

from .models import Disciplina, Docente


class BaseLookup(LookupChannel):
    def _construct_query(self, q):
        return reduce(
            operator.and_, [Q(nome__unaccent__icontains=p) for p in q.split()]
        )

    def get_query(self, q, request):
        return self.model.objects.filter(self._construct_query(q))[:10]


@register("c_docentes")
class DocenteLookup(BaseLookup):
    model = Docente


@register("c_disciplinas")
class DisciplinaLookup(BaseLookup):
    model = Disciplina
