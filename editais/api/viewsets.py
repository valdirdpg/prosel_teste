from rest_framework import viewsets

from editais.api import serializers
from editais.models import Edital


class EditalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Edital.objects.filter(publicado=True)
    serializer_class = serializers.EditalSerializer
    filter_fields = ("nome", "numero", "ano")
