import csv
import io
from datetime import datetime
from decimal import Decimal

from csv2py import CSVLoader, DjangoCSVLineLoader, Field
from django.core.files.storage import default_storage

from base.choices import Turno
from base.models import PessoaFisica
from cursos.models import CursoSelecao
from processoseletivo import models


def safe_decimal(value):
    if "," in value:
        value = value.replace(",", ".")
    return Decimal(value)


class ModalidadeSisuLoader(DjangoCSVLineLoader):
    model = models.Modalidade
    context_name = "modalidade"
    unique_attrs = ["nome"]
    fields = [Field(column="NO_MODALIDADE_CONCORRENCIA", target_attribute="nome")]

    def create_object(self, attrs):
        raise ValueError("Não pode criar novas modalidades")

    def get_object(self, key):
        obj = super().get_object(key)

        if obj:
            return obj
        else:
            try:
                m = models.ModalidadeVariavel.objects.get(**key)
                return m.modalidade
            except models.ModalidadeVariavel.DoesNotExist:
                return

    def update_object(self, obj, attrs):
        pass


class CandidatoSisuLoader(DjangoCSVLineLoader):
    context_name = "candidato"
    model = models.Candidato
    unique_attrs = ["cpf"]
    fields = [
        Field(column="NU_CPF_INSCRITO", target_attribute="cpf"),
        Field(column="NU_RG", target_attribute="rg"),
        Field(column="NO_INSCRITO", target_attribute="nome"),
        Field(column="DT_NASCIMENTO", target_attribute="nascimento"),
        Field(column="NO_MAE", target_attribute="nome_mae"),
        Field(column="DS_LOGRADOURO", target_attribute="logradouro"),
        Field(column="NU_ENDERECO", target_attribute="numero_endereco"),
        Field(column="DS_COMPLEMENTO", target_attribute="complemento_endereco"),
        Field(column="SG_UF_INSCRITO", target_attribute="uf"),
        Field(column="NO_MUNICIPIO", target_attribute="municipio"),
        Field(column="NO_BAIRRO", target_attribute="bairro"),
        Field(column="NU_CEP", target_attribute="cep"),
        Field(
            column="NU_FONE1", target_attribute="telefone2", null=True
        ),  # NU_FONE1 e telefone2 é o tel. fixo
        Field(
            column="NU_FONE2", target_attribute="telefone", null=True
        ),  # NU_FONE2 e telefone é o tel. celular
        Field(column="DS_EMAIL", target_attribute="email"),
    ]

    def clean_nome(self, value):
        return value.upper()

    def clean_nascimento(self, value):
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

    def clean_cpf(self, value):
        if "." in value or "-" in value:
            return value

        value = value.zfill(11)
        return f"{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:11]}"

    def clean_bairro(self, value):
        if "-----" in value:
            return ""
        return value

    def clean_cep(self, value):

        if "." in value or "-" in value:
            return value

        value = value.zfill(8)
        return f"{value[:2]}.{value[2:5]}-{value[5:]}"

    def clean_telefone(self, value):

        if not value:
            return None

        value = value.replace(" ", "")

        if len(value) < 9:
            return None

        if "(" in value or "-" in value:
            return value

        if len(value) == 9:
            return f"({value[:2]}){value[2:5]}-{value[5:]}"
        elif len(value) == 10:
            return f"({value[:2]}){value[2:6]}-{value[6:]}"
        elif len(value) == 11:
            return f"({value[:2]}){value[2:7]}-{value[7:]}"
        else:
            raise ValueError("Quantidade de dígitos")

    def clean_telefone2(self, value):
        return self.clean_telefone(value)

    def get_object(self, key):
        try:
            cpf = key["cpf"]
            return self.model.objects.get(pessoa__cpf=cpf)
        except self.model.DoesNotExist:
            return

    def create_object(self, attrs):
        cpf = attrs["cpf"]
        qs = PessoaFisica.objects.filter(cpf=cpf)
        if not qs.exists():
            pessoa = PessoaFisica.objects.get_or_create(**attrs)[0]
        else:
            pessoa = qs.first()
        return self.model.objects.get_or_create(pessoa=pessoa)[0]

    def update_object(self, obj, attrs):
        PessoaFisica.objects.filter(id=obj.pessoa_id).update(**attrs)


class InscricaoSisuLoader(DjangoCSVLineLoader):
    model = models.Inscricao
    context_name = "inscricao"
    context_requires = ("edicao", "modalidade", "candidato")
    unique_attrs = ("edicao", "modalidade", "candidato", "curso")
    fields = [
        Field(column="DS_TURNO", target_attribute="turno"),
        Field(column="CO_IES_CURSO", target_attribute="codigo", type=int),
    ]

    def get_data(self):
        attrs = super().get_data()
        turno_map = dict(t[::-1] for t in Turno.choices())
        curso = CursoSelecao.objects.get(
            codigo=attrs["codigo"], turno=turno_map[attrs["turno"]]
        )
        attrs["curso"] = curso
        attrs.pop("codigo")
        attrs.pop("turno")
        return attrs


class DesempenhoSisuLoader(DjangoCSVLineLoader):
    model = models.Desempenho
    context_name = "desempenho"
    context_requires = ("inscricao",)
    unique_attrs = context_requires
    fields = [
        Field(
            column="NU_NOTA_L", target_attribute="nota_em_linguas", type=safe_decimal
        ),
        Field(
            column="NU_NOTA_CH", target_attribute="nota_em_humanas", type=safe_decimal
        ),
        Field(
            column="NU_NOTA_CN",
            target_attribute="nota_em_ciencias_naturais",
            type=safe_decimal,
        ),
        Field(
            column="NU_NOTA_M", target_attribute="nota_em_matematica", type=safe_decimal
        ),
        Field(
            column="NU_NOTA_R", target_attribute="nota_na_redacao", type=safe_decimal
        ),
        Field(
            column="NU_NOTA_CANDIDATO", target_attribute="nota_geral", type=safe_decimal
        ),
        Field(column="NU_CLASSIFICACAO", target_attribute="classificacao", type=int),
    ]

    def run(self):
        super().run()
        inscricao = self.context["inscricao"]
        desempenho = self.context["desempenho"]
        if inscricao.modalidade_id != models.ModalidadeEnum.ampla_concorrencia:
            inscricao.pk = None
            inscricao.modalidade = models.Modalidade.objects.get(
                id=models.ModalidadeEnum.ampla_concorrencia
            )
            inscricao.save(force_insert=True)

            desempenho.pk = None
            desempenho.inscricao = inscricao
            desempenho.save(force_insert=True)


class SisuLoader(CSVLoader):
    reader_class = csv.DictReader
    line_loaders = [
        ModalidadeSisuLoader,
        CandidatoSisuLoader,
        InscricaoSisuLoader,
        DesempenhoSisuLoader,
    ]

    def after_line_loader(self, line, context):

        if context.get("skip_vagas"):
            return

        vagas = int(line["QT_VAGAS_CONCORRENCIA"])
        if vagas:
            if not models.Vaga.objects.filter(
                edicao=context["edicao"],
                curso=context["inscricao"].curso,
                modalidade=context["modalidade"],
            ).exists():
                models.Vaga.criar_varias(
                    vagas,
                    edicao=context["edicao"],
                    curso=context["inscricao"].curso,
                    modalidade=context["modalidade"],
                )

    def open(self, filename, encoding):
        file = default_storage.open(filename)
        return io.StringIO(file.read().decode(encoding), newline="\r")
