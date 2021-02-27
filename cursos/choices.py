from base.choices import BaseChoice


class Formacao(BaseChoice):
    INTEGRADO = "Técnico Integrado"
    SUBSEQUENTE = "Técnico Subsequente"
    TECNOLOGICO = "Tecnológico"
    BACHARELADO = "Bacharelado"
    LICENCIATURA = "Licenciatura"
    ESPECIALIZACAO = "Especialização"
    MESTRADO = "Mestrado"
    DOUTORADO = "Doutorado"
    CONCOMITANTE = "Concomitante"


class NivelFormacao(BaseChoice):
    TECNICO = "Técnico"
    GRADUACAO = "Graduação"
    POSGRADUACAO = "Pós-graduação"


class Modalidade(BaseChoice):
    PRESENCIAL = "Presencial"
    EAD = "A distância"
    SEMIPRESENCIAL = "Semipresencial"


class RegimeTrabalho(BaseChoice):
    DE = "Dedicação Exclusiva"
    TI = "Tempo Integral (40h)"
    TP = "Tempo Parcial (20h)"
