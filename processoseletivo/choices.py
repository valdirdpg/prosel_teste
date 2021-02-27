from base.choices import BaseChoice


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
