from rest_framework import serializers

from editais import models


class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Documento
        fields = ("nome", "categoria", "arquivo", "data_upload")


class PeriodoSelecaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PeriodoSelecao
        fields = ("nome", "inicio", "fim")


class EditalSerializer(serializers.ModelSerializer):
    processo_seletivo = serializers.HyperlinkedRelatedField(
        source="edicao.processo_seletivo",
        view_name="processoseletivo-detail",
        read_only=True,
    )
    cronograma_selecao = PeriodoSelecaoSerializer(
        many=True, source="cronogramas_selecao"
    )
    documentos = DocumentoSerializer(many=True)

    class Meta:
        model = models.Edital
        fields = (
            "url",
            "nome",
            "processo_seletivo",
            "numero",
            "ano",
            "cronograma_selecao",
            "documentos",
        )
