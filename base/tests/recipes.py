from django.contrib.auth.models import Group, User
from faker import Faker
from model_mommy.recipe import Recipe, seq

from .. import models

faker = Faker("pt_BR")

user = Recipe(
    User,
    username=seq("user"),
    first_name=faker.first_name_male,
    last_name=faker.last_name,
    email=faker.email,
    is_staff=False,
    is_superuser=False
)

group = Recipe(
    Group,
    name=seq("Grupo ")
)

pessoa_fisica = Recipe(
    models.PessoaFisica,
    nome=faker.name,
    cpf=faker.cpf,
    bairro=faker.neighborhood,
    numero_endereco=faker.building_number,
    municipio=faker.city,
    logradouro=faker.street_name,
    uf=faker.state_abbr,
)
