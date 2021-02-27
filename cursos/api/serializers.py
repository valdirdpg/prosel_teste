from rest_framework import serializers

from cursos import models


class Documento(serializers.ModelSerializer):
    tipo = serializers.CharField(source="tipo.nome")

    class Meta:
        model = models.Documento
        exclude = ("id", "curso")


class CidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cidade
        exclude = ("id",)


class CampusSerializer(serializers.HyperlinkedModelSerializer):
    cidade = CidadeSerializer()
    cursos = serializers.HyperlinkedRelatedField(
        many=True,
        source="cursonocampus_set",
        read_only=True,
        view_name="cursonocampus-detail",
    )

    class Meta:
        model = models.Campus
        exclude = ("aparece_no_menu", "mapa", "ies", "servidores")


class DocenteSerializer(serializers.ModelSerializer):
    regime_trabalho = serializers.CharField(source="rt")
    disciplinas = serializers.HyperlinkedRelatedField(
        many=True,
        source="disciplinacurso_set",
        view_name="disciplinacurso-detail",
        read_only=True,
    )

    class Meta:
        model = models.Servidor
        exclude = ("matricula", "rt", "id")


class CursoNoCampusSerializer(serializers.HyperlinkedModelSerializer):
    nome = serializers.CharField(source="curso.nome")
    nivel_formacao = serializers.CharField(source="curso.nivel_formacao")
    disciplinas = serializers.HyperlinkedRelatedField(
        many=True,
        source="disciplinacurso_set",
        view_name="disciplinacurso-detail",
        read_only=True,
    )
    documentos = Documento(many=True, source="documento_set")

    class Meta:
        model = models.CursoNoCampus
        exclude = ("palavras_chave", "curso", "codigo_suap")


class DisciplinaCursoSerializer(serializers.HyperlinkedModelSerializer):
    nome = serializers.CharField(source="disciplina.nome")

    class Meta:
        model = models.DisciplinaCurso
        exclude = ("disciplina",)
