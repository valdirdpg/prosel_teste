from itertools import cycle

from faker import Faker
from model_mommy.recipe import Recipe, seq, foreign_key

from . import models, choices

faker = Faker('pt_BR')

ies = Recipe(
    models.IES,
    codigo=seq(1),
    uf=faker.estado_sigla,
    nome=seq("Instituto Federal "),
    sigla=seq("IF"),
)

campus = Recipe(
    models.Campus,
    nome=seq("Campus "),
    sigla=seq("CP "),
    ies=foreign_key(ies),
    cidade__nome=faker.city,
    cidade__uf=faker.estado_sigla,
    endereco=faker.street_name,
    telefone=seq("83 9999 999"),
    url=faker.url,
)

curso = Recipe(
    models.Curso,
    nome=seq("Curso "),
    perfil_unificado=faker.sentence(nb_words=10),
)

curso_tecnico = curso.extend(
    nivel_formacao=choices.NivelFormacao.TECNICO.name
)

curso_graduacao = curso.extend(
    nivel_formacao=choices.NivelFormacao.GRADUACAO.name
)

cursonocampus = Recipe(
    models.CursoNoCampus,
    campus=foreign_key(campus),
    curso=foreign_key(curso),
)

cursonocampus_subsequente = cursonocampus.extend(
    curso=foreign_key(curso_tecnico),
    formacao=choices.Formacao.SUBSEQUENTE.name
)

curso_selecao = Recipe(
    models.CursoSelecao,
    campus=foreign_key(campus),
    curso=foreign_key(curso),
)

curso_selecao_subsequente = curso_selecao.extend(
    curso=foreign_key(curso_tecnico),
    formacao=choices.Formacao.SUBSEQUENTE.name
)

curso_selecao_graduacao = curso_selecao.extend(
    curso=foreign_key(curso_graduacao),
    formacao=cycle(
        [
            choices.Formacao.BACHARELADO.name,
            choices.Formacao.TECNOLOGICO.name,
            choices.Formacao.LICENCIATURA.name,
        ]
    )
)

polo = Recipe(
    models.Polo,
    horario_funcionamento='10:00',
    endereco=faker.street_name,
    telefone=seq("83 9999 999")
)
