from cursos import models as cursos_models
from processoseletivo import models as p_models

from psct import models


def get_candidato(candidato: models.Candidato):
    qs = p_models.Candidato.objects.filter(pessoa__cpf=candidato.cpf)

    if qs.exists():
        return qs.first()
    else:
        return p_models.Candidato.objects.create(pessoa=candidato)


def get_modalidade(modalidade: models.Modalidade):
    return modalidade.equivalente


def get_inscricao(resultado_inscricao: models.ResultadoPreliminarInscricao):
    inscricao = resultado_inscricao.inscricao
    candidato = get_candidato(inscricao.candidato)
    modalidade = get_modalidade(inscricao.modalidade_cota)
    ampla = p_models.Modalidade.objects.get(
        id=p_models.ModalidadeEnum.ampla_concorrencia
    )
    edicao = inscricao.edital.edicao
    i = p_models.Inscricao.objects.get_or_create(
        candidato=candidato, curso=inscricao.curso, modalidade=modalidade, edicao=edicao
    )[0]
    if modalidade != ampla:
        # duplica inscrição cotista na ampla
        i2 = p_models.Inscricao.objects.get_or_create(
            candidato=candidato, curso=inscricao.curso, modalidade=ampla, edicao=edicao
        )[0]

    defaults = dict(
        nota_em_linguas=models.ZERO,
        nota_em_humanas=models.ZERO,
        nota_em_ciencias_naturais=models.ZERO,
        nota_em_matematica=models.ZERO,
        nota_na_redacao=models.ZERO,
        nota_geral=resultado_inscricao.inscricao_preanalise.pontuacao,
        classificacao=resultado_inscricao.classificacao,
    )

    p_models.Desempenho.objects.update_or_create(defaults=defaults, inscricao=i)

    if modalidade != ampla:
        p_models.Desempenho.objects.update_or_create(defaults=defaults, inscricao=i2)

    return i


def insert_vagas(dados_vagas: models.ModalidadeVagaCursoEdital):
    edicao = dados_vagas.curso_edital.edital.edicao
    curso = dados_vagas.curso_edital.curso
    modalidade = get_modalidade(dados_vagas.modalidade)
    p_models.Vaga.criar_varias(
        dados_vagas.quantidade_vagas, edicao=edicao, curso=curso, modalidade=modalidade
    )


def export(resultado: models.ResultadoPreliminar):
    edicao = resultado.fase.edital.edicao

    qs = models.ModalidadeVagaCursoEdital.objects.filter(
        curso_edital__edital=resultado.fase.edital
    )

    p_models.Vaga.objects.filter(edicao=edicao).delete()
    for dados in qs:
        insert_vagas(dados)

    for resultado_inscricao in models.ResultadoPreliminarInscricao.objects.filter(
        resultado_curso__resultado=resultado
    ).distinct():
        get_inscricao(resultado_inscricao)

    edicao.importado = True
    edicao.save()

    for campus in cursos_models.Campus.objects.filter(
        cursonocampus__cursoselecao__resultadopreliminarcurso__resultado=resultado
    ).distinct():
        etapa, created = p_models.Etapa.objects.update_or_create(
            edicao=edicao, campus=campus, numero=0, defaults=dict(multiplicador=1)
        )

        if not created:
            p_models.Chamada.objects.filter(etapa=etapa).delete()

        etapa.gerar_chamadas()

    for curso in resultado.fase.edital.processo_inscricao.cursos.all():
        for modalidade in models.Modalidade.objects.all():
            p_modalidade = get_modalidade(modalidade)
            vagas = p_models.Vaga.objects.filter(
                curso=curso, modalidade=p_modalidade, edicao=edicao
            ).count()
            resultado_curso = models.ResultadoPreliminarCurso.objects.get(
                resultado=resultado, curso=curso
            )
            models.VagasResultadoPreliminar.objects.update_or_create(
                resultado_curso=resultado_curso,
                modalidade=modalidade,
                defaults=dict(quantidade=vagas),
            )


def get_inscricoes(
    resultado: models.ResultadoPreliminar,
    curso: models.CursoSelecao,
    modalidade: models.Modalidade,
):
    edital = resultado.fase.edital
    modalidade = get_modalidade(modalidade)
    etapa = edital.edicao.etapa_set.filter(campus=curso.campus, numero=0).first()
    try:
        chamada = p_models.Chamada.objects.get(
            etapa=etapa, curso=curso, modalidade=modalidade
        )
        candidatos = set(
            chamada.inscricoes.values_list(
                "candidato__pessoa__cpf", flat=True
            ).distinct()
        )
        return models.ResultadoPreliminarInscricao.objects.filter(
            inscricao__candidato__cpf__in=candidatos,
            resultado_curso__resultado=resultado,
        ).distinct()
    except p_models.Chamada.DoesNotExist:
        return models.ResultadoPreliminarInscricao.objects.none()
