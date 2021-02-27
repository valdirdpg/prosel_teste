from celery import shared_task
from django.contrib.auth.models import User
from django.db import transaction
from django.urls import reverse

from monitoring.models import PortalTask
from psct import export
from psct.models import analise as analise_models
from psct.models import resultado as models
from psct.models.inscricao import Modalidade, ModalidadeVagaCursoEdital
from psct.render import driver


@shared_task(name="Resultado preliminar PSCT", base=PortalTask)
def gerar_resultado_preliminar(fase_id):
    fase = analise_models.FaseAnalise.objects.get(id=fase_id)
    inscricoes = {}

    with transaction.atomic():
        resultado = models.ResultadoPreliminar.objects.create(fase=fase)

        for curso in fase.edital.processo_inscricao.cursos.all():
            resultado_curso = models.ResultadoPreliminarCurso.objects.create(
                resultado=resultado, curso=curso
            )
            qs = analise_models.InscricaoPreAnalise.objects.filter(
                fase=fase,
                curso=curso,
                situacao=analise_models.SituacaoInscricao.DEFERIDA.name,
            )

            for index, inscricao in enumerate(qs, 1):
                inscricoes[inscricao.id] = models.ResultadoPreliminarInscricao(
                    resultado_curso=resultado_curso,
                    classificacao=index,
                    inscricao_preanalise=inscricao,
                    inscricao=inscricao.inscricao,
                )

            for modalidade in Modalidade.objects.all():
                qs = analise_models.InscricaoPreAnalise.objects.filter(
                    fase=fase,
                    curso=curso,
                    modalidade=modalidade,
                    situacao=analise_models.SituacaoInscricao.DEFERIDA.name,
                )
                for index, inscricao in enumerate(qs, 1):
                    r = inscricoes[inscricao.id]
                    r.classificacao_cota = index

        models.ResultadoPreliminarInscricao.objects.bulk_create(inscricoes.values())

        qs = analise_models.InscricaoPreAnalise.objects.filter(
            fase=fase, situacao=analise_models.SituacaoInscricao.INDEFERIDA.name
        )

        inscricoes_indeferidas = []
        for inscricao in qs:
            inscricoes_indeferidas.append(
                models.ResultadoPreliminarInscricaoIndeferida(
                    resultado=resultado,
                    inscricao_preanalise=inscricao,
                    inscricao=inscricao.inscricao,
                    justiticativa_indeferimento=inscricao.motivo_indeferimento,
                )
            )

        models.ResultadoPreliminarInscricaoIndeferida.objects.bulk_create(
            inscricoes_indeferidas
        )

        export.export(
            resultado
        )  # exporta os dados pro processo seletivo e gera as chamadas

    return {
        "url": reverse("admin:psct_resultadopreliminar_changelist"),
        "message": "O resultado foi gerado com sucesso!",
    }


@shared_task(name="Resultado preliminar PSCT com 2a opção", base=PortalTask)
def gerar_resultado_preliminar_segunda_opcao(fase_id):
    fase = analise_models.FaseAnalise.objects.get(id=fase_id)

    with transaction.atomic():
        resultado = models.ResultadoPreliminar.objects.create(fase=fase)
        inscricoes_qs = analise_models.InscricaoPreAnalise.objects.filter(
            fase=fase, situacao=analise_models.SituacaoInscricao.DEFERIDA.name,
        ).order_by(
            "-pontuacao",
            "-pontuacao_pt",
            "-pontuacao_mt",
            "nascimento",
            "-modalidade__equivalente",
        )
        proxima_posicao = {}
        resultados_inscricoes = []

        for inscricao in inscricoes_qs:

            # testa a primeira opcao
            contemplado = False
            chave_vaga = inscricao.curso, inscricao.modalidade

            if chave_vaga not in proxima_posicao:
                proxima_posicao[chave_vaga] = 1

            resultado_curso, _ = models.ResultadoPreliminarCurso.objects.get_or_create(
                resultado=resultado, curso=inscricao.curso
            )

            vagas_totais = ModalidadeVagaCursoEdital.objects.get(
                modalidade=inscricao.modalidade,
                curso_edital__curso=inscricao.curso,
                curso_edital__edital=inscricao.fase.edital,
            ).quantidade_vagas

            proxima_vaga = proxima_posicao[chave_vaga]
            if proxima_vaga <= vagas_totais:
                resultado_inscricao = models.ResultadoPreliminarInscricao(
                    resultado_curso=resultado_curso,
                    classificacao=proxima_vaga,
                    inscricao_preanalise=inscricao,
                    inscricao=inscricao.inscricao,
                )
                resultados_inscricoes.append(resultado_inscricao)
                proxima_posicao[chave_vaga] += 1
                contemplado = True
            elif inscricao.curso_segunda_opcao:
                chave_vaga = (inscricao.curso_segunda_opcao, inscricao.modalidade)

                if chave_vaga not in proxima_posicao:
                    proxima_posicao[chave_vaga] = 1

                (
                    resultado_curso_segunda_opcao,
                    _,
                ) = models.ResultadoPreliminarCurso.objects.get_or_create(
                    resultado=resultado, curso=inscricao.curso_segunda_opcao
                )

                vagas_totais_segunda_opcao = ModalidadeVagaCursoEdital.objects.get(
                    modalidade=inscricao.modalidade,
                    curso_edital__curso=inscricao.curso_segunda_opcao,
                    curso_edital__edital=inscricao.fase.edital,
                ).quantidade_vagas

                proxima_vaga_segunda_opcao = proxima_posicao[chave_vaga]

                if proxima_vaga_segunda_opcao <= vagas_totais_segunda_opcao:
                    resultado_inscricao = models.ResultadoPreliminarInscricao(
                        resultado_curso=resultado_curso_segunda_opcao,
                        classificacao=proxima_vaga_segunda_opcao,
                        inscricao_preanalise=inscricao,
                        inscricao=inscricao.inscricao,
                    )
                    resultados_inscricoes.append(resultado_inscricao)
                    proxima_posicao[chave_vaga] += 1
                    contemplado = True

            if not contemplado:
                resultado_inscricao = models.ResultadoPreliminarInscricao(
                    resultado_curso=resultado_curso,
                    classificacao=proxima_vaga,
                    inscricao_preanalise=inscricao,
                    inscricao=inscricao.inscricao,
                )
                resultados_inscricoes.append(resultado_inscricao)

        models.ResultadoPreliminarInscricao.objects.bulk_create(resultados_inscricoes)

        qs = analise_models.InscricaoPreAnalise.objects.filter(
            fase=fase, situacao=analise_models.SituacaoInscricao.INDEFERIDA.name
        )

        inscricoes_indeferidas = []
        for inscricao in qs:
            inscricoes_indeferidas.append(
                models.ResultadoPreliminarInscricaoIndeferida(
                    resultado=resultado,
                    inscricao_preanalise=inscricao,
                    inscricao=inscricao.inscricao,
                    justiticativa_indeferimento=inscricao.motivo_indeferimento,
                )
            )

        models.ResultadoPreliminarInscricaoIndeferida.objects.bulk_create(
            inscricoes_indeferidas
        )

        export.export(
            resultado
        )  # exporta os dados pro processo seletivo e gera as chamadas

    return {
        "url": reverse("admin:psct_resultadopreliminar_changelist"),
        "message": "O resultado foi gerado com sucesso!",
    }


@shared_task(name="Exportar resultado PSCT para arquivo", ignore_results=True)
def exportar_resultado_arquivo(user_id, resultado_id, render_id, filetype):
    resultado = models.ResultadoPreliminar.objects.get(id=resultado_id)
    user = User.objects.get(id=user_id)

    driver_class = driver.get_driver(filetype)
    driver_obj = driver_class(resultado, render_id)
    driver_obj.run()
    driver_obj.report(user)
