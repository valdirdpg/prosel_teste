from django.db.models import F
from django.db.models.functions import Upper
from rest_framework import viewsets

from processoseletivo import models
from processoseletivo.api import permissions
from processoseletivo.api import serializers


class ProcessoSeletivoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.ProcessoSeletivo.objects.all()
    serializer_class = serializers.ProcessoSeletivoSerializer
    filter_fields = ("nome", "sigla")


class CandidatoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        models.PessoaFisica.objects.annotate(nome_normalizado=Upper(F("nome")))
        .exclude(candidato_ps=None)
        .all()
    )
    serializer_class = serializers.PessoaFisicaSerializer
    filter_fields = ("cpf",)
    permission_classes = (permissions.IsMemberOfGroup,)
    group_required = "API - Web Service SUAP"
