from faker import Faker
from model_mommy.recipe import Recipe

from . import models

faker = Faker("pt_BR")

processo_seletivo = Recipe(
    models.ProcessoSeletivo
)

edicao = Recipe(models.Edicao)
