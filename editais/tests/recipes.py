import datetime

from faker import Faker
from model_mommy.recipe import foreign_key, Recipe, seq

from .. import choices
from .. import models

faker = Faker("pt_BR")

edital = Recipe(
    models.Edital,
    nome=seq("Edital "),
    numero=seq(1),
    ano=seq(2000),
    publicado=True,
    descricao=faker.sentence,
)

edital_abertura = edital.extend(tipo=choices.EditalChoices.ABERTURA.name)

documento = Recipe(models.Documento, edital=foreign_key(edital), nome=seq("Documento "))

periodo_selecao = Recipe(
    models.PeriodoSelecao,
    edital=foreign_key(edital),
    nome=seq("Periodo de seleção "),
    inicio=datetime.date.today,
    fim=datetime.date.today,
    tipo=choices.CronogramaChoices.SELECAO.name,
)

periodo_convocacao = Recipe(models.PeriodoConvocacao)

nivel_selecao = Recipe(
    models.NivelSelecao,
    edital=foreign_key(edital),
    nome=seq("Nível de seleção "),
    vagas=1,
    valor_inscricao=10,
)

cronograma = Recipe(
    models.Cronograma,
    nome=seq("Cronograma "),
    inicio=datetime.date.today,
    fim=datetime.date.today,
)
