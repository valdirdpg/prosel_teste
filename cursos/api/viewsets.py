from rest_framework import viewsets

from cursos import models
from cursos.api import filters
from cursos.api import serializers
from cursos.api.paginators import CursoNoCampusPagination


class CampiViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Campus.objects.all()
    serializer_class = serializers.CampusSerializer
    filter_class = filters.CampusFilter


class DocenteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Servidor.objects.docentes()
    serializer_class = serializers.DocenteSerializer
    filter_class = filters.DocenteFilter


class DisciplinaCursoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.DisciplinaCurso.objects.filter(curso__publicado=True).distinct()
    serializer_class = serializers.DisciplinaCursoSerializer
    filter_class = filters.DisciplinaFilter


class CursoNoCampusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.CursoNoCampus.objects.filter(publicado=True)
    serializer_class = serializers.CursoNoCampusSerializer
    pagination_class = CursoNoCampusPagination
    filter_class = filters.CursoNoCampusFilter
