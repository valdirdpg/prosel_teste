from base.choices import BaseChoice


class CronogramaChoices(BaseChoice):
    SELECAO = "Seleção"
    CONVOCACAO = "Convocação"


class EventoCronogramaChoices(BaseChoice):
    INTERESSE = "Manifestação de Interesse"
    ANALISE = "Análise de documentação"
    CONFIRMACAO = "Confirmação de matrícula"
    OUTRO = "Outro"


class EditalChoices(BaseChoice):
    ABERTURA = "Abertura"
    RETIFICACAO = "Retificação"


class CategoriaDocumentoChoices(BaseChoice):
    RESULTADO = "Resultado"
    PROVA = "Prova"
    GABARITO = "Gabarito"
    EDITAL = "Edital"
    RECURSO = "Recurso"
    LOCALPROVA = "Local de Prova"
    ANEXO = "Anexo"
