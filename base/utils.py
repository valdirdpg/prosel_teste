import os
import re
from datetime import datetime

from bs4 import BeautifulSoup as BS
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from base.configs import PortalConfig


def get_src_mapa(mapa):
    """
    Extrai o atributo src do componente html (iframe) passado como parâmetro.
    :param mapa: tag <iframe>
    :return: o valor do atributo src (https://...) ou uma string vazia.
    """
    try:
        result = BS(mapa, "html.parser")
        return result.iframe.attrs["src"]
    except:
        return ""


def join_by(value, arg):
    """

    :param value:
    :param arg:
    :return:
    """
    value = list(str(x) for x in value)
    return arg.join(value)


def human_list(my_list, separator=", ", last_separator=" e "):
    """
    Human readable list.
    :param my_list: a list de things
    :param separator: separator used between items of list
    :param last_separator:
    :return:
    """
    my_list = list(my_list)
    if len(my_list) == 0:
        return ""
    elif len(my_list) == 1:
        return f"{my_list[0]}"
    first_part = my_list[:-1]
    last_part = my_list[-1]
    first_part = separator.join(str(x) for x in first_part)
    return f"{first_part}{last_separator}{last_part}"


def dias_entre(inicio, fim):
    """
    Calcula a quantidade de dias entre duas datas.
    Aceita objetos datetime.date e datetime.datetime.
    :param inicio:
    :param fim:
    :return:
    """
    if not all([inicio, fim]):
        raise ValidationError(_("Datas de início ou fim não foram informadas."))
    if isinstance(inicio, datetime):
        inicio = inicio.date()
    if isinstance(fim, datetime):
        fim = fim.date()
    dias = (fim - inicio).days
    return dias


class CPF:
    error_messages = {
        "invalid": _("Inválido."),
        "digits_only": _("Deve conter apenas números."),
        "num_digits": _("Deve possuir exatamente 11 números."),
    }

    def __init__(self, cpf):
        """Classe representando um número de CPF
        a = CPF('95524361503')
        b = CPF('955.243.615-03')
        c = CPF([9, 5, 5, 2, 4, 3, 6, 1, 5, 0, 3])
        """

        if isinstance(cpf, list):
            cpf = "".join(map(str, cpf))

        if isinstance(cpf, str):
            cpf = re.sub(r"[-\.]", "", cpf)  # retira pontos e traços
            if not cpf.isdigit():
                raise ValidationError(self.error_messages["digits_only"])

        if len(cpf) != 11:
            raise ValidationError(self.error_messages["num_digits"])

        self.cpf = cpf

    def format(self):
        return CPF.format_number(self.cpf)

    def valido(self):
        return CPF.validate_number(self.cpf)

    @staticmethod
    def format_number(cpf):
        """
        Method that formats a brazilian CPF
        Tests:
        print Cpf().format('91289037736')
        912.890.377-36
        """
        return f"{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"

    @staticmethod
    def validate_number(value):
        """
        Valida o cpf passado como parâmetro ou o próprio objeto.
        Tests:
        >> a = CPF('95524361503')
        >> a.validate()
        True
        >>

        912.890.377-36
        """
        cpf = value
        cpf_invalidos = [11 * str(i) for i in range(10)]
        if cpf in cpf_invalidos:
            return False

        selfcpf = [int(x) for x in cpf]
        cpf = selfcpf[:9]
        while len(cpf) < 11:
            r = (
                sum(
                    [
                        (len(cpf) + 1 - i) * v
                        for i, v in [(x, cpf[x]) for x in range(len(cpf))]
                    ]
                )
                % 11
            )
            if r > 1:
                f = 11 - r
            else:
                f = 0
            cpf.append(f)
        return bool(cpf == selfcpf)

    def __getitem__(self, index):
        """Retorna o dígito em index como string
        >> a = CPF('95524361503')
        >> a[9] == '0'
        True
        >> a[10] == '3'
        True
        >> a[9] == 0
        False
        >> a[10] == 3
        False
        """
        return str(self.cpf[index])

    def __repr__(self):
        """Retorna uma representação 'real', ou seja:
        eval(repr(cpf)) == cpf
        >> a = CPF('95524361503')
        >> print repr(a)
        CPF('95524361503')
        >> eval(repr(a)) == a
        True
        """
        return f"CPF('{''.join([str(x) for x in self.cpf])}')"

    def __eq__(self, other):
        """Provê teste de igualdade para números de CPF
        >> a = CPF('95524361503')
        >> b = CPF('955.243.615-03')
        >> c = CPF('123.456.789-00')
        >> a == b
        True
        >> a != c
        True
        >> b != c
        True
        """

        try:
            other = CPF(other)
        except:
            pass

        if isinstance(other, CPF):
            return self.cpf == other.cpf
        else:
            return False

    def __str__(self):
        """Retorna uma string do CPF na forma com pontos e traço
        >> a = CPF('95524361503')
        >> str(a)
        '955.243.615-03'
        """
        return self.format()

    def __bool__(self):
        return self.valido()


def file_extension(file):
    *name, extension = os.path.splitext(file.name)
    return extension


def normalizar_nome_proprio(nome, siglas=None):
    """
    Normaliza o nome próprio dado, aplicando a capitalização correta de acordo
    com as regras e exceções definidas no código.

    OBS.: Adaptado do código-fonte do SUAP: djtools/utils.py
    """
    ponto = r"\."
    ponto_espaco = ". "
    espaco = " "
    regex_multiplos_espacos = r"\s+"
    regex_numero_romano = "^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$"

    nome = re.sub(ponto, ponto_espaco, nome)  # colocando espaço após nomes abreviados
    nome = re.sub(regex_multiplos_espacos, espaco, nome)  # retirando espaços múltiplos
    nome = nome.title()  # alterando os nomes para CamelCase
    partes_nome = nome.split(espaco)  # separando as palavras numa lista
    excecoes = [
        "de",
        "di",
        "do",
        "da",
        "dos",
        "das",
        "dello",
        "della",
        "dalla",
        "dal",
        "del",
        "e",
        "em",
        "na",
        "no",
        "nas",
        "nos",
        "van",
        "von",
        "y",
        "a",
        "o",
        "à",
        "ao",
    ]

    resultado = []

    for palavra in partes_nome:
        if palavra != partes_nome[0] and palavra.lower() in excecoes:
            resultado.append(palavra.lower())
        elif re.match(regex_numero_romano, palavra.upper()):
            resultado.append(palavra.upper())
        elif siglas and palavra.upper() in siglas:
            resultado.append(palavra.upper())
        else:
            resultado.append(palavra)

    nome = espaco.join(resultado)
    return nome


def simplificar_titulacao(codigo=None, titulacao=None):
    """
    Simplifica todas as titulações do SUAP em cinco grupos:
    Graduação, Aperfeiçoamento, Especialização, Mestrado e Doutorado.
    :param codigo: string com o código (coluna 'codigo' da tabela 'titulacao' do SUAP
    :param titulacao: string com a titulação a ser simplificada, obtida do SUAP
    :return: string com a simplificação em um dos cinco grupos.
    """

    from base.choices import Titulacao

    nao_classificados = {
        "20": "TECNICO (NIVEL MEDIO COMPLETO)",
        "21": "APERFEICOAMENTO NIVEL MEDIO",
        "22": "ESPECIALIZACAO NIVEL MEDIO",
        "29": "ALTOS ESTUDOS (RMI)",
        "30": "APERFEICOAMENTO (RMI)",
        "31": "ESPECIALIZACAO (RMI)",
        "32": "FORMACAO (RMI)",
        "33": "AUXILIAR DE ENFERMAGEM",
        "36": "POS-GRADUACAO",
        "45": "NIVEL MÉDIO",
        "55": "CURSOS EQUIPARADOS - GQ - 360 HORAS",
        "46": "ENSINO FUNDAMENTAL",
        "47": "SOLOS E NUTRICAO DE PLANTAS",
        "38": "APERFEICOAMENTO PROFISSIONAL DE NS",
        "51": "CURSO QUALIFICACAO PROFISSIONAL MIN 180H",
        "52": "CURSO QUALIFICACAO PROFISSIONAL MIN 250H",
        "53": "CURSO QUALIFICACAO PROFISSIONAL MIN 360H",
        "54": "CURSO CAPACIT/QUALIFIC PROFISSI MIN 180H",
        "01": "PROFISSIONAL EM MAT EM REDE NACIONAL",
    }

    graduacao = {
        "23": "GRADUACAO (NIVEL SUPERIOR COMPLETO)",
        "37": "BACHAREL",
        "48": "GRADUAÇÃO+RSC-I (LEI 12772/12 ART. 18)",
        "34": "LICENCIATURA PLENA",
        "35": "LICENCIATURA",
    }

    aperfeicoamento = {
        "24": "APERFEICOAMENTO NIVEL SUPERIOR",
        "39": "APERFEICOAMENTO - NA",
        "41": "APERFEICOAMENTO - NA",
        "43": "APERFEICOAMENTO - NA",
    }

    especializacao = {
        "25": "ESPECIALIZACAO NIVEL SUPERIOR",
        "40": "ESPECIALIZACAO - NA",
        "42": "ESPECIALIAZACA - NA",
        "44": "ESPECIALIZACAO - NA",
        "49": "POS-GRADUAÇÃO+RSC-II LEI 12772/12 ART 18",
    }

    mestrado = {"26": "MESTRADO", "50": "MESTRE+RSC-III (LEI 12772/12 ART 18)"}

    doutorado = {"27": "DOUTORADO", "36": "POS-DOUTORADO"}

    if titulacao in graduacao.values() or codigo in graduacao.keys():
        return Titulacao.GRADUACAO.name
    elif titulacao in aperfeicoamento.values() or codigo in aperfeicoamento.keys():
        return Titulacao.APERFEICOAMENTO.name
    elif titulacao in especializacao.values() or codigo in especializacao.keys():
        return Titulacao.ESPECIALIZACAO.name
    elif titulacao in mestrado.values() or codigo in mestrado.keys():
        return Titulacao.MESTRADO.name
    elif titulacao in doutorado.values() or codigo in doutorado.keys():
        return Titulacao.DOUTORADO.name
    elif titulacao in nao_classificados.values() or codigo in nao_classificados.keys():
        return Titulacao.NAODEFINIDO.name
    else:
        return Titulacao.NAOINFORMADO.name


def exists(*args):
    return all(args)


def retirar_simbolos_cpf(cpf):
    return re.sub(r"[-\.]", "", cpf)


def is_maior_idade(nascimento):
    """
    Calcula se algúem é maior de idade com base na sua data de nascimento.
    :param nascimento: data de nascimento
    :return: bool
    """
    if not nascimento:
        raise ValidationError(_("Data de nascimento não foi informada."))
    if isinstance(nascimento, datetime):
        nascimento = nascimento.date()

    anos = idade(nascimento)
    return anos >= PortalConfig.MAIORIDADE


def idade(nascimento, data=None):
    """
    Calcula a idade de uma pessoa com base na sua data de nascimento.
    :param nascimento: date
    :param data: date (assume o dia de hoje, caso não seja informado)
    :return: int
    """
    if not nascimento:
        raise ValidationError(_("Data de nascimento não foi informada."))
    elif isinstance(nascimento, datetime):
        nascimento = nascimento.date()
    if not data:
        data = datetime.now().date()
    elif isinstance(data, datetime):
        data = data.date()
    anos = data.year - nascimento.year
    meses = data.month - nascimento.month
    if meses < 0 or (meses == 0 and data.day < nascimento.day):
        anos -= 1
    return anos


class TituloEleitor:
    """
    Título de Eleitor Brasileiro.
    É composto por dez números e dois dígitos verificadores, totalizando doze algarismos.
    Os oito primeiros números são sequenciais (part1)
    O nono, décimo e décimo primeiro formam a segunda parte (part2)
    O nono e o décimo números representam o estado onde foram emitidos.
    O décimo primeiro é dígito verificador da primeira parte (dv1)
    O décimo segundo é o digito verificador da segunda parte (dv2)
    """

    error_messages = {
        "invalid": _("Inválido."),
        "digits_only": _("Deve conter apenas números."),
        "num_digits": _("Deve possuir exatamente 12 números."),
    }

    # ZZ = exterior
    uf_code = {
        "01": "SP",
        "02": "MG",
        "03": "RJ",
        "04": "RS",
        "05": "BA",
        "06": "PR",
        "07": "CE",
        "08": "PE",
        "09": "SC",
        "10": "GO",
        "11": "MA",
        "12": "PB",
        "13": "PA",
        "14": "ES",
        "15": "PI",
        "16": "RN",
        "17": "AL",
        "18": "MT",
        "19": "MS",
        "20": "DF",
        "21": "SE",
        "22": "AM",
        "23": "RO",
        "24": "AC",
        "25": "AP",
        "26": "RR",
        "27": "TO",
        "28": "ZZ",
    }

    def __init__(self, numero):
        """Classe representando um Título de Eleitor
        a = TituloEleitor('000000000000')
        b = TituloEleitor('0000 0000 0000')
        c = TituloEleitor([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        """
        if isinstance(numero, list):
            numero = "".join(map(str, numero))

        if isinstance(numero, str):
            numero = re.sub(
                r"[-\.\/\s]", "", numero
            )  # ponto, traço, barra e espaço em branco
            if not numero.isdigit():
                raise ValidationError(self.error_messages["digits_only"])

        if numero and len(numero) != 12:
            raise ValidationError(self.error_messages["num_digits"])

        self.numero = numero

    def format(self):
        return TituloEleitor.format_number(self.numero)

    def valido(self):
        return TituloEleitor.validate_number(self.numero)

    def uf(self):
        return self.uf_code.get(self.numero[8:10])

    @staticmethod
    def format_number(numero):
        """
        Method that formats a brazilian TituloEleitor
        Tests:
        print TituloEleitor().format('912890377367')
        9128 9077 3645
        """
        return f"{numero[0:4]} {numero[4:8]} {numero[8:12]}"

    @staticmethod
    def validate_number(value):
        """
        Valida o número passado como parâmetro ou o próprio objeto.
        Tests:
        >> TituloEleitor.validate_number('955243615034')
        True
        """
        numero = value
        part1 = numero[:8]
        part2 = numero[8:-1]
        count1 = 0
        count2 = 0
        for i, mult1 in enumerate(range(2, 10)):
            count1 += int(part1[i]) * mult1
        for i, mult2 in enumerate(range(7, 10)):
            count2 += int(part2[i]) * mult2
        dv1 = 0 if count1 % 11 == 10 else count1 % 11
        dv2 = 0 if count2 % 11 == 10 else count2 % 11
        return dv1 == int(numero[10]) and dv2 == int(numero[11])

    def __getitem__(self, index):
        """Retorna o dígito em index como string
        >> a = TituloEleitor('95524361503')
        >> a[9] == '0'
        True
        >> a[10] == '3'
        True
        >> a[9] == 0
        False
        >> a[10] == 3
        False
        """
        return str(self.numero[index])

    def __repr__(self):
        """Retorna uma representação 'real', ou seja:
        eval(repr(numero)) == numero
        >> a = TituloEleitor('95524361503')
        >> print repr(a)
        TituloEleitor('95524361503')
        >> eval(repr(a)) == a
        True
        """
        return f"TituloEleitor({self.numero})"

    def __eq__(self, other):
        """Provê teste de igualdade para números de Titulo de Eleitor
        >> a = TituloEleitor('955243615031')
        >> b = TituloEleitor('9552 4361 5031')
        >> c = TituloEleitor('1234 5678 9002')
        >> a == b
        True
        >> a != c
        True
        >> b != c
        True
        """
        try:
            other = TituloEleitor(other)
        except:
            pass

        if isinstance(other, TituloEleitor):
            return self.numero == other.numero
        else:
            return False

    def __str__(self):
        """Retorna uma string do TituloEleitor na forma com espaço
        >> a = TituloEleitor('95524361503')
        >> str(a)
        '9552 4361 5031'
        """
        return self.format()

    def __bool__(self):
        return self.valido()
