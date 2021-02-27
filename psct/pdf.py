import os
from datetime import datetime

from django.conf import settings
from django.shortcuts import get_object_or_404

from base import pdf
from cursos.models import CursoSelecao
from processoseletivo.models import ModalidadeEnum
from psct.models import inscricao as inscricao_models


def imprimir_comprovante(request, inscricao_pk, chave):

    inscricao = get_object_or_404(inscricao_models.Inscricao, id=inscricao_pk)
    edital = inscricao.edital
    pontuacao = inscricao.pontuacao if hasattr(inscricao, 'pontuacao') else None
    candidato = inscricao.candidato
    solicitante = request.user.get_full_name()

    """
    Retorna o PdfReport referente ao parâmetro ****
    """
    documento = []

    # cabecalho
    image_logo_path = os.path.join(
        settings.BASE_DIR, "templates", "publico", "img", "logo-ifba-new.jpg"
    )
    image_logo = pdf.Image(image_logo_path, width=49.6 * pdf.mm, height=13.0 * pdf.mm)
    if edital.processo_inscricao.is_graduacao:
        formacao = "SUPERIORES"
    else:
        formacao = "TÉCNICOS"

    str_cabecalho = (
        
        f"<font size=9>PROCESSO SELETIVO PARA CURSOS {formacao} - EDITAL Nº "
        f"{edital.numero}/{edital.ano}</font><br/><b>Comprovante de Inscrição</b><br/>"
    )
    tbl_cabecalho = pdf.table(
        rows=[[image_logo, str_cabecalho]],
        a=["c", "c"],
        w=[50, 135],
        grid=0,
        fontSize=12,
    )

    documento.append(tbl_cabecalho)
    documento.append(pdf.space(5))
    documento.append(pdf.para("<b>DADOS GERAIS</b>", style="Italic", size="8"))
    documento.append(pdf.space(1))
    dados_gerais = []
    dados_gerais.append(["<b>Número de inscrição:</b>", f"{inscricao.id}"])
    dados_gerais.append(["<b>Candidato:</b>", f"{candidato.nome}"])
    dados_gerais.append(["<b>CPF:</b>", f"{candidato.cpf}"])
    dados_gerais.append(["<b>E-mail:</b>", f"{candidato.email}"])
    dados_gerais.append(["<b>Telefone:</b>", f"{candidato.telefone}"])
    dados_gerais.append(
        ["<b>Data de Nascimento:</b>", f"{candidato.nascimento.strftime('%d/%m/%Y')}",]
    )
    dados_gerais.append(
        ["<b>Nome da Mãe ou do(a) Responsável:</b>", f"{candidato.nome_responsavel}",]
    )
    dados_gerais.append(["<b>Sexo:</b>", f"{candidato.get_sexo_display()}"])
    dados_gerais.append(["<b>Nacionalidade:</b>", f"{candidato.nacionalidade}"])
    dados_gerais.append(
        ["<b>Município de nascimento:</b>", f"{candidato.naturalidade}"]
    )
    dados_gerais.append(
        ["<b>Estado de nascimento:</b>", f"{candidato.naturalidade_uf}"]
    )
    propriedades_tabela = dict(a=["l", "l"], w=[65, 120], grid=1, zebra=1, fontSize=8)
    documento.append(pdf.table(dados_gerais, **propriedades_tabela))
    documento.append(pdf.space(5))
    if edital.processo_inscricao.possui_segunda_opcao:
        if inscricao.curso_segunda_opcao:
            titulo_opcao = "DADOS DA VAGA (1ª OPÇÃO)"
        else:
            titulo_opcao = "DADOS DA VAGA (OPÇÃO ÚNICA *)"
    else:
        titulo_opcao = "DADOS DA VAGA"

    documento.append(pdf.para(f"<b>{titulo_opcao}</b>", style="Italic", size="8"))
    documento.append(pdf.space(1))
    documento.append(
        pdf.table(
            _create_box_curso(inscricao.curso, inscricao),
            **propriedades_tabela
        )
    )

    if edital.processo_inscricao.possui_segunda_opcao:
        if inscricao.curso_segunda_opcao:
            documento.append(pdf.space(5))
            documento.append(
                pdf.para("<b>DADOS DA VAGA (2ª OPÇÃO)</b>", style="Italic", size="8"))
            documento.append(pdf.space(1))
            documento.append(
                pdf.table(
                    _create_box_curso(inscricao.curso_segunda_opcao, inscricao),
                    **propriedades_tabela
                )
            )
        else:
            documento.append(pdf.space(1))
            documento.append(
                pdf.para(
                    "* Candidato não selecionou segunda opção de curso.",
                    style="Italic",
                    size="8"
                )
            )

    documento.append(pdf.space(5))
    if pontuacao:
        documento.append(
            pdf.para("<b>PONTUAÇÃO DA INSCRIÇÃO</b>", style="Italic", size="8")
        )
        documento.append(pdf.space(1))
        documento.append(pdf.table(_create_box_pontuacao(pontuacao), **propriedades_tabela))

    # rodapé
    datahora = datetime.now()
    str_rodape = [
        "<b>Gerado em:</b> {} às {}".format(
            datahora.strftime("%d/%m/%Y"), datahora.strftime("%H:%M:%S")
        ),
        "Para verificar a autenticidade deste comprovante, utilize o código: <b><i>{}</i></b>".format(
            chave
        ),
    ]
    rodape = {
        "height": 7,
        "story": [
            pdf.table([str_rodape], a=["l", "r"], w=[55, 140], grid=0, fontSize=8)
        ],
    }

    return pdf.PdfReport(body=documento, footer_args=rodape, pages_count=1).generate()


def _create_box_curso(curso, inscricao) -> list:
    dados_vaga = []
    dados_vaga.append(["<b>Campus:</b>", f"{curso.campus}"])
    if curso.polo:
        dados_vaga.append(["<b>Polo:</b>", f"{curso.polo}"])

    dados_vaga.append(
        ["<b>Tipo de Formação:</b>", f"{curso.get_formacao_display()}"]
    )
    dados_vaga.append(["<b>Curso:</b>", f"{curso.curso.nome}"])
    dados_vaga.append(["<b>Turno:</b>", f"{curso.get_turno_display()}"])

    if inscricao.modalidade_cota.equivalente.is_ampla_concorrencia():
        dados_vaga.append(["<b>Modalidade de Cota:</b>", "Nenhuma"])
    else:
        dados_vaga.append(
            ["<b>Concorre às vagas: </b>",
             f"{inscricao.modalidade_cota.por_nivel_formacao(inscricao.processo_inscricao)}"]
             # "(Toda/o candidata/o, mesmo cotista, concorre também pela Ampla Concorrência)"]
        )
    return dados_vaga


def _create_box_pontuacao(pontuacao) -> list:
    dados_pontuacao = []
    dados_pontuacao.append(["<b>Pontuação Total:</b>", f"{pontuacao.valor}"])
    dados_pontuacao.append(["<b>Pontuação em Português:</b>", f"{pontuacao.valor_pt}"])
    dados_pontuacao.append(["<b>Pontuação em Matemática:</b>", f"{pontuacao.valor_mt}"])
    if pontuacao.inscricao.is_integrado:
        dados_pontuacao.append(
            [
                "<b>Pontuação em História:</b>",
                f"{pontuacao.get_pontuacao_historia_display()}",
            ]
        )
        dados_pontuacao.append(
            [
                "<b>Pontuação em Geografia:</b>",
                f"{pontuacao.get_pontuacao_geografia_display()}",
            ]
        )
    if pontuacao.is_curso_graduacao:
        dados_pontuacao.append(
            [
                "<b>Pontuação em Redação:</b>",
                f"{pontuacao.valor_redacao}",
            ]
        )
    return dados_pontuacao


def lista_inscritos_pdf(edital, queryset_inscricoes, final=False, campus=None):

    """
    Retorna o PdfReport referente ao parâmetro ****
    """
    documento = []

    # cabecalho
    image_logo_path = os.path.join(
        settings.BASE_DIR, "templates", "publico", "img", "logo-ifba-new.jpg"
    )
    image_logo = pdf.Image(image_logo_path, width=49.6 * pdf.mm, height=13.0 * pdf.mm)
    str_cabecalho = (
        
        f"EDITAL Nº {edital.numero}/{edital.ano}<br/>"
        f'<b>RELAÇÃO {"FINAL" if final else "PRELIMINAR"} DE CANDIDATOS INSCRITOS</b>'        f"{edital.edicao.processo_seletivo.nome.upper()} - "

    )
    if campus:
        str_cabecalho = f"{str_cabecalho}<br/><b>CAMPUS {campus.nome.upper()}</b>"
    tbl_cabecalho = pdf.table(
        rows=[[image_logo, str_cabecalho]],
        a=["c", "c"],
        w=[50, 145],
        grid=0,
        fontSize=10,
    )
    documento.append(tbl_cabecalho)
    documento.append(pdf.space(15))

    # tabela de legenda das modalidades
    documento.append(
        pdf.para("<b>Legenda para a modalidade de cota:</b>", alignment="left", size=8)
    )
    modalidades = inscricao_models.Modalidade.objects.order_by("texto").exclude(
        equivalente_id=ModalidadeEnum.ampla_concorrencia
    )
    texto_legenda_modalidades = ""
    posicoes_modalidade = {}
    for posicao, modalidade in enumerate(modalidades, 1):
        posicoes_modalidade[modalidade.id] = posicao
        texto_legenda_modalidades = (
            f"{texto_legenda_modalidades} <i>{posicao} - "
            f"{str(modalidade.por_nivel_formacao(edital.processo_inscricao))}</i>  <br/>"
        )
    documento.append(pdf.para(texto_legenda_modalidades, alignment="left", size=7))
    documento.append(pdf.space(10))

    # Uma tabela por curso
    cursos_selecao = CursoSelecao.objects.filter(
        processoinscricao__edital=edital
    ).distinct()
    if campus:
        cursos_selecao = cursos_selecao.filter(campus=campus)

    totalizador_campus = 0
    for curso in cursos_selecao:
        documento.append(pdf.para(f"<b>{curso}</b>", alignment="left", size=8))
        documento.append(pdf.space(1))
        labels = [
            "<b>Inscrição</b>",
            "<b>Nome</b>",
            "<b>Curso</b>",
            "<b>Campus</b>",
            "<b>Cota</b>",
        ]
        if curso.polo:
            labels[3] = f"<b>Campus/Polo</b>"

        tabela = [labels]
        inscricoes_curso = queryset_inscricoes.filter(curso=curso)
        if campus:
            inscricoes_curso = inscricoes_curso.filter(curso__campus=campus)
        for inscricao in inscricoes_curso:
            modalidade = (
                "Não"
                if inscricao.modalidade_cota.is_ampla
                else f"{(posicoes_modalidade[inscricao.modalidade_cota.id])}"
            )
            linha = [
                f"{inscricao.id}",
                f"{inscricao.nome_normalizado}",
                f"{inscricao.curso.curso.nome} - {inscricao.curso.turno}".upper(),
                f"{inscricao.curso.campus}".upper(),
                modalidade,
            ]
            if curso.polo:
                linha[3] = f"{linha[3]}/{inscricao.curso.polo}".upper()

            tabela.append(linha)

        documento.append(
            pdf.table(
                tabela,
                a=["c", "l", "l", "l", "c"],
                w=[20, 70, 50, 30, 15],
                head=1,
                grid=1,
                zebra=1,
                fontSize=8,
            )
        )
        totalizador_curso = inscricoes_curso.count()
        total = (
            f"<b> Total de candidatos com inscrições concluídas "
            f"em {curso}: {totalizador_curso}</b>"
        )
        documento.append(pdf.para(total, size=8))
        documento.append(pdf.space(5))
        totalizador_campus += totalizador_curso

    total = f"<b> Total de candidatos com inscrições concluídas: {totalizador_campus}</b>"
    documento.append(pdf.para(total, size=8))

    # tabela de legenda das modalidades
    documento.append(
        pdf.para("<b>Legenda para a modalidade de cota:</b>", alignment="left", size=8)
    )
    documento.append(pdf.para(texto_legenda_modalidades, alignment="left", size=7))
    documento.append(pdf.space(10))

    # rodapé
    datahora = datetime.now()
    rodape = {
        "height": 5,
        "story": [
            pdf.para(
                "<b>Gerado em:</b> {} às {}".format(
                    datahora.strftime("%d/%m/%Y"), datahora.strftime("%H:%M:%S")
                ),
                alignment="left",
                size=8,
            )
        ],
    }

    return pdf.PdfReport(body=documento, footer_args=rodape, pages_count=1).generate()


def resultado_recursos_pdf(fase, queryset_recursos):

    """
    Retorna o PdfReport referente ao parâmetro ****
    """
    documento = []

    # cabecalho
    image_logo_path = os.path.join(
        settings.BASE_DIR, "templates", "publico", "img", "logo-ifba-new.jpg"
    )
    image_logo = pdf.Image(image_logo_path, width=49.6 * pdf.mm, height=13.0 * pdf.mm)
    str_cabecalho = (
        
        f"PROCESSO SELETIVO PARA CURSOS TÉCNICOS - "
        f"EDITAL Nº {fase.edital.numero}/{fase.edital.ano}<br/>"
        f"<b>RESULTADO DE {fase.nome.upper()}</b>"
    )
    tbl_cabecalho = pdf.table(
        rows=[[image_logo, str_cabecalho]],
        a=["c", "c"],
        w=[50, 145],
        grid=0,
        fontSize=10,
    )
    documento.append(tbl_cabecalho)
    documento.append(pdf.space(15))

    # tabela da listagem dos candidatos
    tabela = [
        [
            "<b>Inscrição</b>",
            "<b>Nome</b>",
            "<b>Curso</b>",
            "<b>Campus</b>",
            "<b>Situação</b>",
        ]
    ]

    totalizador = 0
    for index, recurso in enumerate(queryset_recursos):
        parecer = recurso.pareceres_homologadores.last()

        tabela.append(
            [
                f"{recurso.inscricao.id}",
                f"{recurso.nome_normalizado}",
                "{} - {}".format(
                    recurso.inscricao.curso.curso.nome, recurso.inscricao.curso.turno
                ).upper(),
                f"{recurso.inscricao.curso.campus}".upper(),
                f"{parecer.status}",
            ]
        )
        totalizador = index

    documento.append(
        pdf.table(
            tabela,
            a=["c", "l", "l", "l", "c"],
            w=[20, 70, 50, 30, 25],
            head=1,
            grid=1,
            zebra=1,
            fontSize=8,
        )
    )

    total = f"<b> Total de recursos: {(totalizador + 1)}</b>"
    documento.append(pdf.para(total))

    # rodapé
    datahora = datetime.now()
    rodape = {
        "height": 5,
        "story": [
            pdf.para(
                "<b>Gerado em:</b> {} às {}".format(
                    datahora.strftime("%d/%m/%Y"), datahora.strftime("%H:%M:%S")
                ),
                alignment="left",
                size=8,
            )
        ],
    }

    return pdf.PdfReport(body=documento, footer_args=rodape, pages_count=1).generate()
