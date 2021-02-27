import operator
from functools import reduce

from ajax_select import LookupChannel, register
from django.db.models import Q

from . import models


class BaseLookup(LookupChannel):
    model = None
    nome_field = None

    def _construct_query(self, q):
        search_key = f"{self.nome_field}__unaccent__icontains"
        return reduce(operator.and_, [Q(**{search_key: p}) for p in q.split()])

    def get_query(self, q, request):
        return self.model.objects.filter(self._construct_query(q))[:10]


@register("ps_candidatos")
class CandidatoLookup(BaseLookup):
    model = models.Candidato
    nome_field = "pessoa__nome"

    def format_item_display(self, obj):
        return f"{obj.pessoa.nome} (CPF: {obj.pessoa.cpf})"


@register("ps_inscricoes")
class InscricaoLookup(BaseLookup):
    model = models.Inscricao
    nome_field = "candidato__pessoa__nome"

    def get_query(self, q, request):
        return self.model.objects.filter(
            self._construct_query(q), chamada__etapa__encerrada=False
        ).distinct()[:10]


@register("ps_confirmacoes")
class ConfirmacaoLookup(BaseLookup):
    model = models.ConfirmacaoInteresse
    nome_field = "inscricao__candidato__pessoa__nome"

    def get_query(self, q, request):
        return self.model.objects.filter(
            self._construct_query(q), etapa__encerrada=False
        ).distinct()[:10]


@register("ps_analises")
class AnaliseLookup(BaseLookup):
    model = models.AnaliseDocumental
    nome_field = "confirmacao_interesse__inscricao__candidato__pessoa__nome"

    def get_query(self, q, request):
        return self.model.objects.filter(
            self._construct_query(q),
            situacao_final=False,
            confirmacao_interesse__etapa__encerrada=False,
        ).distinct()[:10]
