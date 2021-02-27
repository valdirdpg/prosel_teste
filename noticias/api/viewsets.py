from rest_framework import viewsets

from noticias import models
from noticias.api import serializers


class NoticiaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Noticia.objects.filter(publicado=True)
    serializer_class = serializers.NoticiaSerializer
