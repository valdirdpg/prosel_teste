from datetime import date, timedelta

from faker import Faker
from model_mommy.recipe import foreign_key, Recipe, seq

import base.tests.recipes
import cursos.recipes
from .. import models
from ..choices import Status, StatusRecurso

faker = Faker('pt_BR')

processo_seletivo = Recipe(
    models.ProcessoSeletivo,
    nome=seq('Processo Seletivo '),
    sigla=seq('PS')
)

edicao = Recipe(
    models.Edicao,
    nome=seq("Edição "),
    processo_seletivo=foreign_key(processo_seletivo),
    ano=date.today().year
)

etapa = Recipe(
    models.Etapa,
    edicao=foreign_key(edicao),
    numero=seq(1)
)

vaga = Recipe(
    models.Vaga,
    edicao=foreign_key(edicao),
)

chamada = Recipe(
    models.Chamada,
    etapa=foreign_key(etapa),
    multiplicador=1,
    vagas=10
)

candidato = Recipe(
    models.Candidato,
    pessoa=foreign_key(base.tests.recipes.pessoa_fisica)
)

inscricao = Recipe(
    models.Inscricao,
    edicao=foreign_key(edicao),
    chamada=foreign_key(chamada),
    candidato=foreign_key(candidato),
    curso=foreign_key(cursos.recipes.curso_selecao),
)

matricula = Recipe(
    models.Matricula,
    inscricao=foreign_key(inscricao),
    etapa=foreign_key(etapa)
)

confirmacao = Recipe(
    models.ConfirmacaoInteresse,
    etapa=foreign_key(etapa),
    inscricao=foreign_key(inscricao)
)

resultado = Recipe(
    models.Resultado,
    inscricao=foreign_key(inscricao),
    etapa=foreign_key(etapa),
    status=Status.DEFERIDO.name,
    observacao=faker.paragraph(1, variable_nb_sentences=False)
)

analise = Recipe(
    models.AnaliseDocumental,
    confirmacao_interesse=foreign_key(confirmacao),
    servidor_coordenacao=faker.name,
    observacao=faker.paragraph(1, variable_nb_sentences=False),
    data=date.today() - timedelta(days=1),
    situacao_final=True
)

recurso = Recipe(
    models.Recurso,
    analise_documental=foreign_key(analise),
    protocolo=seq("Protocolo "),
    justificativa=faker.paragraph(1, variable_nb_sentences=False),
    status_recurso=StatusRecurso.DEFERIDO.name
)

desempenho = Recipe(
    models.Desempenho,
    inscricao=foreign_key(inscricao),
    classificacao=seq(1)
)

tipo_analise = Recipe(
    models.TipoAnalise,
    nome=seq("Tipo de análise "),
    setor_responsavel=seq("Setor responsável ")
)

modalidade = Recipe(
    models.Modalidade,
    nome=seq('Modalidade '),
    resumo=seq('Resumo da modalidade ')
)

modalidade_variavel = Recipe(
    models.ModalidadeVariavel,
    modalidade=foreign_key(modalidade),
    nome=seq('Modalidade variável ')
)

avaliacao = Recipe(
    models.AvaliacaoDocumental,
    tipo_analise=foreign_key(tipo_analise),
    analise_documental=foreign_key(analise),
    servidor_setor=faker.name,
    data=date.today(),
    situacao=True
)
