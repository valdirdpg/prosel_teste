import django_filters

from cursos import models


class DocenteFilter(django_filters.rest_framework.FilterSet):
    nome_contem = django_filters.CharFilter(
        name="nome", lookup_expr="unaccent__icontains", label="Nome contém"
    )

    class Meta:
        model = models.Servidor
        fields = ("nome", "nome_contem", "titulacao")


class CampusFilter(django_filters.rest_framework.FilterSet):
    nome_contem = django_filters.CharFilter(
        name="nome", lookup_expr="unaccent__icontains", label="Nome contém"
    )

    class Meta:
        model = models.Campus
        fields = ("nome", "nome_contem")


class DisciplinaFilter(django_filters.rest_framework.FilterSet):
    nome_contem = django_filters.CharFilter(
        name="disciplina__nome", lookup_expr="unaccent__icontains", label="Nome contém"
    )

    class Meta:
        model = models.DisciplinaCurso
        fields = ("nome_contem",)


class CursoNoCampusFilter(django_filters.rest_framework.FilterSet):
    nome_contem = django_filters.CharFilter(
        name="curso__nome", lookup_expr="unaccent__icontains", label="Nome contém"
    )

    class Meta:
        model = models.CursoNoCampus
        fields = ("nome_contem",)
