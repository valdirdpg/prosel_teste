from rest_framework import serializers

from candidatos.models import Caracterizacao
from processoseletivo import models


class EdicaoSerializer(serializers.HyperlinkedModelSerializer):
    editais = serializers.HyperlinkedRelatedField(
        many=True, view_name="edital-detail", source="edital_set", read_only=True
    )

    class Meta:
        model = models.Edicao
        fields = ("nome", "ano", "semestre", "status", "editais")


class ProcessoSeletivoSerializer(serializers.ModelSerializer):
    edicoes = EdicaoSerializer(many=True)

    class Meta:
        model = models.ProcessoSeletivo
        fields = ("nome", "sigla", "descricao", "imagem", "edicoes")


class EdicaoInlineSerializer(serializers.ModelSerializer):
    processo_seletivo = serializers.CharField(source="processo_seletivo.sigla")
    matriculado = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        self.pessoa = kwargs.pop("pessoa")
        super().__init__(*args, **kwargs)

    class Meta:
        model = models.Edicao
        fields = ("processo_seletivo", "ano", "semestre", "nome", "matriculado")

    def get_matriculado(self, obj):
        return models.Matricula.objects.filter(
            inscricao__candidato__pessoa=self.pessoa, etapa__edicao=obj
        ).exists()


class CaracterizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caracterizacao
        exclude = ["candidato"]
        depth = 1


class PessoaFisicaSerializer(serializers.HyperlinkedModelSerializer):
    nome = serializers.CharField(source="nome_normalizado")
    aprovacoes = serializers.SerializerMethodField()
    caracterizacoes = CaracterizacaoSerializer(many=True, source="caracterizacao_set")
    tipo_sanguineo = serializers.SerializerMethodField()
    tipo_zona_residencial = serializers.SerializerMethodField()
    parentesco_responsavel = serializers.SerializerMethodField()

    class Meta:
        model = models.PessoaFisica
        exclude = ["user"]

    def get_aprovacoes(self, obj):
        qs = models.Edicao.objects.filter(
            etapa__chamadas__inscricoes__candidato=obj.candidato_ps
        ).distinct()
        serializer = EdicaoInlineSerializer(instance=qs, many=True, pessoa=obj)
        return serializer.data

    def get_tipo_sanguineo(self, obj):
        return {"name": obj.get_tipo_sanguineo_display(), "value": obj.tipo_sanguineo}

    def get_tipo_zona_residencial(self, obj):
        return {
            "name": obj.get_tipo_zona_residencial_display(),
            "value": obj.tipo_zona_residencial,
        }

    def get_parentesco_responsavel(self, obj):
        return {
            "name": obj.get_parentesco_responsavel_display(),
            "value": obj.parentesco_responsavel,
        }
