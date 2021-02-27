import datetime
from itertools import cycle

from django.utils import timezone
from faker import Faker
from model_mommy.recipe import foreign_key, Recipe, related, seq

import base.tests.recipes
from base.choices import Nacionalidade
from cursos.choices import Formacao
from cursos.recipes import curso_selecao
from editais.tests.recipes import edital
from .. import models

faker = Faker('pt_BR')

candidato = Recipe(
    models.Candidato,
    nome=faker.name_male,
    cpf=faker.cpf,
    nascimento=faker.date_of_birth(minimum_age=17, maximum_age=70),
    nacionalidade=Nacionalidade.BRASILEIRA.name,
    logradouro=faker.street_name,
    numero_endereco=faker.building_number,
    bairro=faker.bairro,
    municipio=faker.city,
    uf=faker.estado_sigla,
    cep=faker.postcode,
    email=faker.email,
    user=foreign_key(base.tests.recipes.user)
)

curso_psct = curso_selecao.extend(
    formacao=cycle(
        [
            Formacao.INTEGRADO.name,
            Formacao.SUBSEQUENTE.name,
        ]
    )
)

processo_inscricao = Recipe(
    models.ProcessoInscricao,
    edital=foreign_key(edital),
    multiplicador=5,
    data_inicio=datetime.date.today,
    data_encerramento=datetime.date.today
)

curso_edital = Recipe(
    models.CursoEdital,
    edital=foreign_key(edital),
    curso=foreign_key(curso_psct)
)

modalidade_padrao = Recipe(
    models.ModalidadePadrao,
    nome=seq("Modalidade padrão "),
    resumo=seq("Resumo da modalidade "),
)

modalidade = Recipe(
    models.Modalidade,
    equivalente=foreign_key(modalidade_padrao),
    texto=seq("Modalidade "),
)

modalidade_vaga_curso_edital = Recipe(
    models.ModalidadeVagaCursoEdital,
    curso_edital=foreign_key(curso_edital),
    modalidade=foreign_key(modalidade),
    quantidade_vagas=1,
    multiplicador=3,
)

criterio_questionario = Recipe(
    models.CriterioQuestionario,
    numero=seq(1),
    descricao_questao=seq("Pergunta ")
)

criterio_alternativa = Recipe(
    models.CriterioAlternativa,
    posicao=seq(1),
    criterio=foreign_key(criterio_questionario),
    descricao_alternativa=seq("Alternativa "),
)

modelo_questionario = Recipe(
    models.ModeloQuestionario,
    edital=foreign_key(edital),
    nome=seq("Modelo "),
    itens_avaliados=related(criterio_questionario)
)

inscricao = Recipe(
    models.Inscricao,
    candidato=foreign_key(candidato),
    edital=foreign_key(edital),
    aceite=True,
    curso=foreign_key(curso_psct),
    modalidade_cota=foreign_key(modalidade)
)

pontuacao_inscricao = Recipe(models.PontuacaoInscricao, inscricao=foreign_key(inscricao))

nota_anual = Recipe(models.NotaAnual, pontuacao=foreign_key(pontuacao_inscricao))

comprovante = Recipe(models.Comprovante, inscricao=foreign_key(inscricao), nome=seq("Certificado "))

cancelamento_inscricao = Recipe(
    models.CancelamentoInscricao,
    inscricao=related(inscricao),
    usuario=foreign_key(base.tests.recipes.user)
)

group_psct = base.tests.recipes.group.extend(name=seq("PSCT - Grupo "))

grupo_edital = Recipe(
    models.GrupoEdital,
    grupo=foreign_key(group_psct),
    edital=foreign_key(edital)
)

fase_analise = Recipe(
    models.FaseAnalise,
    nome=seq("Fase de análise "),
    edital=foreign_key(edital),
    data_inicio=timezone.now,
    data_encerramento=timezone.now,
    data_resultado=timezone.now() + datetime.timedelta(days=1),
    quantidade_avaliadores=1,
    requer_homologador=False,
    avaliadores=foreign_key(grupo_edital),
)

inscricao_pre_analise = Recipe(
    models.InscricaoPreAnalise,
    candidato=foreign_key(candidato),
    fase=foreign_key(fase_analise),
    curso=foreign_key(curso_selecao),
    modalidade=foreign_key(modalidade),
    pontuacao=faker.pydecimal(min_value=5.0, max_value=10.0),
    pontuacao_pt=faker.pydecimal(min_value=1.0, max_value=10.0),
    pontuacao_mt=faker.pydecimal(min_value=1.0, max_value=10.0),
    nascimento=faker.date_of_birth(minimum_age=17, maximum_age=70),
)

mailbox_avaliador_inscricao = Recipe(
    models.MailBoxAvaliadorInscricao,
    fase=foreign_key(fase_analise),
    avaliador=foreign_key(base.tests.recipes.user),
)

mailbox_homologador_inscricao = Recipe(
    models.MailBoxHomologadorInscricao,
    fase=foreign_key(fase_analise),
    homologador=foreign_key(base.tests.recipes.user),
)

avaliacao_avaliador = Recipe(
    models.AvaliacaoAvaliador,
    inscricao=foreign_key(inscricao_pre_analise),
    situacao=models.SituacaoAvaliacao.DEFERIDA.name,
    avaliador=foreign_key(base.tests.recipes.user),
    concluida=models.Concluida.SIM.name
)

avaliacao_homologador = Recipe(
    models.AvaliacaoHomologador,
    inscricao=foreign_key(inscricao_pre_analise),
    situacao=models.SituacaoAvaliacao.DEFERIDA.name,
    homologador=foreign_key(base.tests.recipes.user),
)

justificativa_indeferimento = Recipe(
    models.JustificativaIndeferimento,
    edital=foreign_key(edital),
    texto=faker.sentence
)

avaliacao_avaliador_indeferida = avaliacao_avaliador.extend(
    situacao=models.SituacaoAvaliacao.INDEFERIDA.name,
    texto_indeferimento=foreign_key(justificativa_indeferimento)
)

indeferimento_especial = Recipe(
    models.IndeferimentoEspecial,
    inscricao=foreign_key(inscricao_pre_analise),
    motivo_indeferimento=foreign_key(justificativa_indeferimento),
    autor=foreign_key(base.tests.recipes.user)
)

progresso_analise = Recipe(
    models.ProgressoAnalise,
    fase=foreign_key(fase_analise),
    curso=foreign_key(curso_selecao),
    meta=5
)

fase_ajuste_pontuacao = Recipe(
    models.FaseAjustePontuacao,
    fase_analise=foreign_key(fase_analise),
    data_inicio=timezone.now,
    data_encerramento=timezone.now,
    avaliadores=foreign_key(grupo_edital),
    homologadores=foreign_key(grupo_edital),
)

pilha_inscricao_ajuste = Recipe(
    models.PilhaInscricaoAjuste,
    fase=foreign_key(fase_ajuste_pontuacao)
)

resultado_preliminar = Recipe(
    models.ResultadoPreliminar,
    fase=foreign_key(fase_analise)
)

resultado_preliminar_curso = Recipe(
    models.ResultadoPreliminarCurso,
    resultado=foreign_key(resultado_preliminar),
    curso=foreign_key(curso_selecao),
)

resultado_preliminar_inscricao = Recipe(
    models.ResultadoPreliminarInscricao,
    resultado_curso=foreign_key(resultado_preliminar_curso),
    inscricao_preanalise=foreign_key(inscricao_pre_analise),
    inscricao=foreign_key(inscricao),
    classificacao=seq(1),
    classificacao_cota=seq(1),
)

resultado_preliminar_inscricao_indeferida = Recipe(
    models.ResultadoPreliminarInscricaoIndeferida,
    inscricao=foreign_key(inscricao),
    resultado=foreign_key(resultado_preliminar),
)

vagas_resultado_preliminar = Recipe(
    models.VagasResultadoPreliminar,
    resultado_curso=foreign_key(resultado_preliminar_curso),
    modalidade=foreign_key(modalidade),
    quantidade=1
)

resultado_preliminar_homologado = Recipe(
    models.ResultadoPreliminarHomologado,
    edital=foreign_key(edital),
    resultado=foreign_key(resultado_preliminar),
)

resultado_final = Recipe(
    models.ResultadoFinal,
    edital=foreign_key(edital),
    resultado=foreign_key(resultado_preliminar),
)

coluna = Recipe(
    models.Coluna,
    nome=seq("Coluna "),
    query_string=faker.word,
)
