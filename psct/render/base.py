import abc

from psct.models import resultado
from psct.render.register import register


class ResultadoRenderer(metaclass=abc.ABCMeta):
    description = None

    def __init__(self, resultado):
        self.resultado = resultado

    @abc.abstractproperty
    def title(self):
        pass

    @abc.abstractmethod
    def get_queryset(self, curso, modalidade):
        pass

    def get_columns(self, modalidade):
        if modalidade.is_ampla:  # ampla concorrência
            return self.get_columns_ampla()
        return self.get_columns_cota()

    @abc.abstractmethod
    def get_columns_ampla(self):
        pass

    @abc.abstractmethod
    def get_columns_cota(self):
        pass

    def get_row(self, resultado_inscricao, modalidade):
        if modalidade.is_ampla:
            return self.get_row_ampla(resultado_inscricao)
        return self.get_row_cota(resultado_inscricao)

    @abc.abstractmethod
    def get_row_ampla(self, resultado_inscricao):
        pass

    @abc.abstractmethod
    def get_row_cota(self, resultado_inscricao):
        pass

    def get_table(self, curso, modalidade):
        table = [self.get_columns(modalidade)]
        for resultado_inscricao in self.get_queryset(curso, modalidade):
            row = self.get_row(resultado_inscricao, modalidade)
            table.append(row)
        return table

    def has_output(self, curso, modalidade):
        vagas = self.resultado.get_vagas(curso, modalidade)
        if not vagas.quantidade:
            return False
        return self.get_queryset(curso, modalidade).exists()

    @classmethod
    def get_id(cls):
        module = cls.__module__
        return module + "." + cls.__qualname__


@register
class ResultadoDivulgacaoRenderer(ResultadoRenderer):
    description = "Resultado Final para divulgação"

    @property
    def title(self):
        return "RESULTADO FINAL"

    def get_queryset(self, curso, modalidade):
        return self.resultado.get_inscricoes(curso, modalidade)

    def get_columns_ampla(self):
        return ["Classificação", "Inscrição", "Nome", "Nota"]

    def get_columns_cota(self):
        return self.get_columns_ampla()

    def get_row_ampla(self, resultado_inscricao):
        return [
            resultado_inscricao.classificacao,
            resultado_inscricao.inscricao_id,
            resultado_inscricao.inscricao.nome.upper(),
            resultado_inscricao.inscricao_preanalise.pontuacao,
        ]

    def get_row_cota(self, resultado_inscricao):
        return [
            resultado_inscricao.classificacao_cota,
            resultado_inscricao.inscricao_id,
            resultado_inscricao.inscricao.nome.upper(),
            resultado_inscricao.inscricao_preanalise.pontuacao,
        ]


@register
class ResultadoPreliminarDivulgacaoRenderer(ResultadoDivulgacaoRenderer):
    description = "Resultado Preliminar para divulgação"

    @property
    def title(self):
        return "RESULTADO PRELIMINAR"


@register
class ListaControleRenderer(ResultadoRenderer):
    description = "Lista de controle interno do resultado"

    @property
    def title(self):
        return "LISTA CONTROLE INTERNO"

    def get_queryset(self, curso, modalidade):
        resultado_curso = resultado.ResultadoPreliminarCurso.objects.get(
            resultado=self.resultado, curso=curso
        )
        if modalidade.is_ampla:
            return resultado_curso.inscricoes.all()
        return resultado_curso.inscricoes.filter(
            inscricao_preanalise__modalidade=modalidade
        ).distinct()

    def get_columns_ampla(self):
        return ["Classificação", "Inscrição", "Nome", "Nota"]

    def get_columns_cota(self):
        return [
            "Classificação Geral",
            "Classificação na Cota",
            "Inscrição",
            "Nome",
            "Nota",
        ]

    def get_row_ampla(self, resultado_inscricao):
        return [
            resultado_inscricao.classificacao,
            resultado_inscricao.inscricao_id,
            resultado_inscricao.inscricao.nome.upper(),
            resultado_inscricao.inscricao_preanalise.pontuacao,
        ]

    def get_row_cota(self, resultado_inscricao):
        return [
            resultado_inscricao.classificacao,
            resultado_inscricao.classificacao_cota,
            resultado_inscricao.inscricao_id,
            resultado_inscricao.inscricao.nome.upper(),
            resultado_inscricao.inscricao_preanalise.pontuacao,
        ]


@register
class ListaGeralRenderer(ResultadoRenderer):
    description = "Lista geral do resultado"

    @property
    def title(self):
        return "LISTA GERAL"

    def get_queryset(self, curso, modalidade):
        resultado_curso = resultado.ResultadoPreliminarCurso.objects.get(
            resultado=self.resultado, curso=curso
        )
        if modalidade.is_ampla:
            return resultado_curso.inscricoes.all()
        return resultado_curso.inscricoes.filter(
            inscricao_preanalise__modalidade=modalidade
        ).distinct()

    def get_columns_ampla(self):
        return ["Classificação", "Inscrição", "Nome", "Situação"]

    def get_columns_cota(self):
        return self.get_columns_ampla()

    def get_row_ampla(self, resultado_inscricao):
        return [
            resultado_inscricao.classificacao,
            resultado_inscricao.inscricao_id,
            resultado_inscricao.inscricao.nome.upper(),
            self.get_situacao(resultado_inscricao, self.resultado.get_ampla()),
        ]

    def get_row_cota(self, resultado_inscricao):
        return [
            resultado_inscricao.classificacao_cota,
            resultado_inscricao.inscricao_id,
            resultado_inscricao.inscricao.nome.upper(),
            self.get_situacao(
                resultado_inscricao, resultado_inscricao.inscricao.modalidade_cota
            ),
        ]

    def get_situacao(self, resultado_inscricao, modalidade):
        vagas = self.resultado.get_vagas(
            resultado_inscricao.inscricao.curso, modalidade
        )
        classificacao = resultado_inscricao.classificacao
        if not modalidade.is_ampla:
            classificacao = resultado_inscricao.classificacao_cota

        if classificacao <= vagas.quantidade:
            return "Classificado"
        elif classificacao <= vagas.get_limite_lista_espera():
            return "Em lista de espera"
        else:
            return "Apto mas não classificado"


@register
class ResultadoDivulgacaoDDERenderer(ResultadoRenderer):
    description = "Lista dos candidatos para DDE's"

    @property
    def title(self):
        return "Listagem DDE's"

    def get_queryset(self, curso, modalidade):
        return self.resultado.get_inscricoes(curso, modalidade)

    def get_columns_ampla(self):
        return ["Nome", "Telefone", "Endereço"]

    def get_columns_cota(self):
        return self.get_columns_ampla()

    def get_row_ampla(self, resultado_inscricao):
        return [
            resultado_inscricao.inscricao.nome.upper(),
            resultado_inscricao.inscricao.candidato.telefone,
            resultado_inscricao.inscricao.candidato.endereco_completo,
        ]

    def get_row_cota(self, resultado_inscricao):
        return self.get_row_ampla(resultado_inscricao)


@register
class ResultadoDivulgacaoCompletoRenderer(ResultadoRenderer):
    description = "Lista geral de candidatos para DDE's, incluindo lista de espera"

    @property
    def title(self):
        return "Listagem Completa DDE's"

    def get_queryset(self, curso, modalidade):
        resultado_curso = resultado.ResultadoPreliminarCurso.objects.get(
            resultado=self.resultado, curso=curso
        )
        if modalidade.is_ampla:
            return resultado_curso.inscricoes.all()
        return resultado_curso.inscricoes.filter(
            inscricao_preanalise__modalidade=modalidade
        ).distinct()

    def get_columns_ampla(self):
        return ["Class.", "Inscrição", "Nome", "Nota", "Telefone", "Email", "Endereço"]

    def get_columns_cota(self):
        return self.get_columns_ampla()

    def get_row_ampla(self, resultado_inscricao):
        return [
            resultado_inscricao.classificacao,
            resultado_inscricao.inscricao.id,
            resultado_inscricao.inscricao.nome.upper(),
            resultado_inscricao.inscricao_preanalise.pontuacao,
            resultado_inscricao.inscricao.candidato.telefone,
            resultado_inscricao.inscricao.candidato.email.lower(),
            resultado_inscricao.inscricao.candidato.endereco_completo,
        ]

    def get_row_cota(self, resultado_inscricao):
        return [
            resultado_inscricao.classificacao_cota,
            resultado_inscricao.inscricao.id,
            resultado_inscricao.inscricao.nome.upper(),
            resultado_inscricao.inscricao_preanalise.pontuacao,
            resultado_inscricao.inscricao.candidato.telefone,
            resultado_inscricao.inscricao.candidato.email.lower(),
            resultado_inscricao.inscricao.candidato.endereco_completo,
        ]


class SpecializedRender:
    def __init__(self, render):
        self.render = render

    def __getattr__(self, item):
        return getattr(self.render, item)
