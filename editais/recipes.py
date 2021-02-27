import datetime

from faker import Faker
from model_mommy.recipe import Recipe, seq

from . import models
from .choices import EditalChoices

faker = Faker('pt_BR')

edital = Recipe(
    models.Edital,
    nome=seq("Edital "),
    numero=seq(1),
    ano=datetime.date.today().year,
    data_publicacao=datetime.date.today,
    encerrado=False,
    publicado=False,
    descricao=faker.sentence,
    prazo_pagamento=datetime.date.today,
    setor_responsavel=seq("SETOR"),
    tipo=EditalChoices.ABERTURA.name
)
