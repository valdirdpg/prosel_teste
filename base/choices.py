from enum import Enum, unique


@unique
class BaseChoice(Enum):
    @classmethod
    def choices(cls, blank=False, empty_label="--------"):
        data = [(key, v.value) for (key, v) in cls.__members__.items()]
        return [("", empty_label)] + data if blank else data

    @classmethod
    def label(cls, chave):
        return dict(cls.choices()).get(chave)


class Cor(BaseChoice):
    VERDE_ESCURO = "verde-escuro"
    AZUL_PETROLEO = "azul-petroleo"
    DOURADO = "dourado"
    ROXO = "roxo"
    MARROM_CLARO = "marrom-claro"
    LARANJA = "laranja"
    VERDE = "verde"


class Turno(BaseChoice):
    MATUTINO = "Matutino"
    VESPERTINO = "Vespertino"
    NOTURNO = "Noturno"
    INTEGRAL = "Integral"
    DIURNO = "Diurno"
    PREDOMINANTEMENTE_MATUTINO = "Predominantemente Matutino"
    PREDOMINANTEMENTE_VESPERTINO = "Predominantemente Vespertino"
    NOTURNO_EVEN_AULAS_SABADO = "Noturno + Eventuais Aulas Sabado"
    NOTURNO_SABADO_VESPERTINO = "Noturno + Sabado Vespertino"


class Titulacao(BaseChoice):
    GRADUACAO = "Graduação"
    APERFEICOAMENTO = "Aperfeiçoamento"
    ESPECIALIZACAO = "Especialização"
    MESTRADO = "Mestrado"
    DOUTORADO = "Doutorado"
    NAOINFORMADO = "Não Informado"
    NAODEFINIDO = "Não Definido"


class Estados(BaseChoice):
    AC = "Acre"
    AL = "Alagoas"
    AP = "Amapa"
    AM = "Amazonas"
    BA = "Bahia"
    CE = "Ceará"
    DF = "Distrito Federal"
    ES = "Espírito Santo"
    GO = "Goiás"
    MA = "Maranhão"
    MT = "Mato Grosso"
    MS = "Mato Grosso do Sul"
    MG = "Minas Gerais"
    PA = "Pará"
    PB = "Paraíba"
    PR = "Paraná"
    PE = "Pernambuco"
    PI = "Piauí"
    RJ = "Rio de Janeiro"
    RN = "Rio Grande do Norte"
    RS = "Rio Grande do Sul"
    RO = "Rondônia"
    RR = "Roraima"
    SC = "Santa Catarina"
    SP = "São Paulo"
    SE = "Sergipe"
    TO = "Tocantis"
    ON = "Outra Nacionalidade"


class Sexo(BaseChoice):
    M = "Masculino"
    F = "Feminino"


class TipoSanguineo(BaseChoice):
    A_POS = "A+"
    B_POS = "B+"
    AB_POS = "AB+"
    O_POS = "O+"
    A_NEG = "A-"
    B_NEG = "B-"
    AB_NEG = "AB-"
    O_NEG = "O-"
    DESCONHECE = "Desconhecido"


class TipoZonaResidencial(BaseChoice):
    URBANA = "Urbana"
    RURAL = "Rural"


class GrauParentesco(BaseChoice):
    PAIS = "Pai/Mãe"
    AVOS = "Avô/Avó"
    TIOS = "Tio/Tia"
    #SOBRINHOS = "Sobrinho/Sobrinha"
    OUTROS = "Outro"


class CertidaoCivil(BaseChoice):
    NASCIMENTO = "Nascimento"
    CASAMENTO = "Casamento"


class Nacionalidade(BaseChoice):
    BRASILEIRA = "Brasileira"
    ESTRANGEIRA = "Estrangeira"


class SalarioMinimo(BaseChoice):
    VALOR = 788


SIM_NAO = ((True, "Sim"), (False, "Não"))


# Choices de Processo Seletivo


class StatusDocumentacao(BaseChoice):
    VALIDO = "VALIDO"
    INVALIDO = "INVALIDO"


class StatusRecurso(BaseChoice):
    DEFERIDO = "DEFERIDO"
    INDEFERIDO = "INDEFERIDO"


class Status(BaseChoice):
    DEFERIDO = "DEFERIDO"
    INDEFERIDO = "INDEFERIDO"
    EXCEDENTE = "EXCEDENTE"


class TipoServidor(BaseChoice):
    TAE = "Técnico administrativo"
    DOCENTE = "Docente"
    DOCENTE_EXTERNO = "Docente externo"
    TERCEIRIZADO = "Prestador de serviços"
