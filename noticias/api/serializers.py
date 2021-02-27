from rest_framework import serializers

from noticias import models


class NoticiaSerializer(serializers.ModelSerializer):
    autor = serializers.CharField(source="responsavel.get_full_name")

    class Meta:
        model = models.Noticia
        fields = (
            "titulo",
            "corpo",
            "resumo",
            "autor",
            "criacao",
            "atualizacao",
            "imagem",
        )
