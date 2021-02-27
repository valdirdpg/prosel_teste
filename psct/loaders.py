import csv
import io
from decimal import Decimal

from csv2py import CSVLoader, DjangoCSVLineLoader, Field

from base.utils import CPF
from .models import inscricao as models


def safe_decimal(value):
    if "," in value:
        value = value.replace(",", ".")
    return Decimal(value)


class CandidatoLoader(DjangoCSVLineLoader):
    context_name = "candidato"
    model = models.Candidato
    unique_attrs = ["cpf"]
    fields = [
        Field(column="CPF", target_attribute="cpf"),
    ]

    def clean_cpf(self, value):
        return str(CPF(value))

    def create_object(self, attrs):
        pass

    def update_object(self, obj, attrs):
        pass


class PontuacaoLoader(DjangoCSVLineLoader):
    context_name = "pontuacao"
    model = models.PontuacaoInscricao
    context_requires = ("edital", "candidato")
    unique_attrs = ["inscricao"]

    def get_object(self, key):
        try:
            inscricao = key["inscricao"]
            return self.model.objects.get(inscricao=inscricao)
        except self.model.DoesNotExist:
            return

    def get_data(self):
        attrs = super().get_data()
        inscricao = models.Inscricao.objects.get(
            candidato=attrs["candidato"],
            edital=attrs["edital"]
        )
        attrs["inscricao"] = inscricao
        attrs.pop("edital")
        attrs.pop("candidato")
        return attrs


class NotaAnualLoader(DjangoCSVLineLoader):
    model = models.NotaAnual
    context_name = "nota_anual"
    context_requires = ("pontuacao", "ano")
    unique_attrs = context_requires
    fields = [
        Field(column="NOTA_L", target_attribute="portugues", type=safe_decimal),
        Field(column="NOTA_M", target_attribute="matematica", type=safe_decimal),
        Field(column="NOTA_CH", target_attribute="ciencias_humanas", type=safe_decimal),
        Field(column="NOTA_CN", target_attribute="ciencias_natureza", type=safe_decimal),
        Field(column="NOTA_R", target_attribute="redacao", type=safe_decimal),
    ]

    def create_object(self, attrs):
        self.model.objects.create(**attrs)

    def run(self):
        super().run()
        pontuacao = self.context["pontuacao"]
        pontuacao.update_pontuacao()


class EnemLoader(CSVLoader):
    reader_class = csv.DictReader
    line_loaders = [CandidatoLoader, PontuacaoLoader, NotaAnualLoader]

    def open(self, file, encoding):
        return io.StringIO(file.read().decode(encoding), newline="\r")
