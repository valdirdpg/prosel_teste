import datetime

from faker import Faker
from model_mommy.recipe import foreign_key, Recipe, seq

from .. import models

faker = Faker("pt_BR")

assunto = Recipe(
    models.Assunto,
    nome=seq("Assunto "),
)

noticia = Recipe(
    models.Noticia,
    titulo=faker.sentence,
    corpo=faker.paragraph,
    resumo=faker.sentence,
    assunto=foreign_key(assunto)
)