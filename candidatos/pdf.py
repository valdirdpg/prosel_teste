import os
from datetime import datetime

from django.conf import settings

from base import models as models_base
from base import pdf, utils
from candidatos.models import Caracterizacao
from processoseletivo.models import Chamada


def imprimir_formulario_matricula(request, candidato_id, chamada_id):
    candidato = models_base.PessoaFisica.objects.get(id=candidato_id)
    caract = Caracterizacao.objects.get(candidato__id=candidato_id)
    chamada = Chamada.objects.select_related("curso", "etapa", "modalidade").get(
        id=chamada_id
    )
    curso = chamada.curso
    cidade = curso.campus.cidade
    nome_curso = f"{curso.get_formacao_display()} em {curso.curso.nome}"

    """
    Retorna o PdfReport referente ao parâmetro ****
    """
    documento = []

    solicitante = request.user

    # cabecalho
    image_path = os.path.join(
        settings.BASE_DIR, "templates", "publico", "img", "logo-ifba-new.jpg"
    )
    image = pdf.Image(image_path, width=49.6 * pdf.mm, height=13.0 * pdf.mm)
    str_cabecalho = (
        f"<b>Formulário de Pré-Matrícula</b><br/><i>Campus {curso.campus.nome}</i>"
    )
    foto = pdf.Rect(width=60, height=60, text="Fotografia")
    documento.append(
        pdf.table(
            rows=[[image, str_cabecalho, foto]],
            a=["c", "l", "r"],
            w=[70, 95, 25],
            grid=0,
            fontSize=12,
        )
    )
    documento.append(pdf.space(1))

    documento.append(
        pdf.table(
            [["<b>INFORMAÇÕES SOBRE A VAGA</b>"]], w=[190], grid=1, head=1, fontSize=8
        )
    )

    if chamada.modalidade.is_ampla_concorrencia():
        cotista = "NÃO"
    else:
        cotista = chamada.modalidade.resumo
    documento.append(
        pdf.table(
            [
                [
                    f"<i>Curso:</i><br/><b>{nome_curso.upper()} ({curso.get_modalidade_display().upper()})</b>"
                ]
            ],
            w=[190],
            grid=1,
            fontSize=8,
        )
    )
    dados_vaga = [
        [
            f"<i>Turno:</i><br/><b>{curso.get_turno_display().upper()}</b>",
            f"<i>Cotista:</i><br/><b>{cotista}</b>",
        ]
    ]
    documento.append(
        pdf.table(dados_vaga, a=["l", "l"], w=[95, 95], grid=1, fontSize=8)
    )

    documento.append(
        pdf.table([["<b>DADOS BÁSICOS</b>"]], w=[190], grid=1, head=1, fontSize=8)
    )

    dados_row_1 = [
        [
            f"<i>Nome: </i><br/><b>{candidato.nome.upper()}</b>",
            f"<i>CPF: </i><br/><b>{candidato.cpf}</b>",
            f'<i>Data de Nasc.: </i><br/><b>{candidato.nascimento.strftime("%d/%m/%Y")}</b>',
            f"<i>Sexo: </i><br/><b>{candidato.sexo}</b>",
            f"<i>Tipo Sanguíneo: </i><br/><b>{candidato.get_tipo_sanguineo_display()}</b>",
        ]
    ]
    documento.append(
        pdf.table(
            dados_row_1,
            a=["l", "l", "l", "l", "l"],
            w=[95, 25, 25, 15, 30],
            grid=1,
            fontSize=8,
        )
    )

    dados_row_2 = [
        [
            f"<i>Certidão Civil de <b>{candidato.get_certidao_tipo_display()}</b>: </i><br/>"
            f"<b>Nº {candidato.certidao}, FL {candidato.certidao_folha} do "
            f"livro {candidato.certidao_livro}</b>",
            f"<i>RG - Órgão Emissor/UF - Data de Emissão: </i><br/>"
            f"<b>{candidato.rg_completo}</b>",
        ]
    ]
    documento.append(
        pdf.table(dados_row_2, a=["l", "l"], w=[95, 95], grid=1, zebra=0, fontSize=8)
    )

    dados_row_3 = [
        [
            f"<i>Título de Eleitor - Zona - Seção: </i><br/><b>{candidato.titulo_eleitor}</b>",
            f"<i>Nacionalidade: </i><br/><b>{candidato.nacionalidade.upper()}</b>",
            f"<i>Naturalidade/UF: </i><br/><b>{candidato.naturalidade_completa}</b>",
        ]
    ]
    documento.append(
        pdf.table(
            dados_row_3, a=["l", "l", "l"], w=[95, 30, 65], grid=1, zebra=0, fontSize=8
        )
    )

    dados_pais = [
        [
            f'<i>Nome do Pai: </i><br/><b>{candidato.nome_pai or "Não Informado"}</b>',
            f'<i>Nome da Mãe: </i><br/><b>{candidato.nome_mae or "Não Informado"}</b>',
        ]
    ]
    documento.append(
        pdf.table(dados_pais, a=["l", "l"], w=[95, 95], grid=1, zebra=0, fontSize=8)
    )

    dados_row_4, dados_row_4_align, dados_row_4_width = [], [], []
    if caract.possui_necessidade_especial:
        necessidades = caract.necessidade_especial.values_list("descricao", flat=True)
        str_necessidades = utils.human_list(necessidades).upper()
        dados_row_4.append(
            [
                f"<i>Etnia: </i><br/><b>{str(caract.raca).upper()}</b>",
                "<i>Pessoa com Deficiência - PcD: </i><br/><b>SIM</b>",
                f"<i>Descrição da Necessidade:</i><br/><b>{str_necessidades}</b>",
            ]
        )
        dados_row_4_align, dados_row_4_width = ["l", "l", "l"], [50, 45, 95]
    else:
        dados_row_4.append(
            [
                f"<i>Etnia: </i><br/><b>{str(caract.raca).upper()}</b>",
                "<i>Pessoa com Deficiência - PcD: </i><br/><b>NÃO</b>",
            ]
        )
        dados_row_4_align, dados_row_4_width = ["l", "l"], [50, 140]
    documento.append(
        pdf.table(
            dados_row_4,
            a=dados_row_4_align,
            w=dados_row_4_width,
            grid=1,
            zebra=0,
            fontSize=8,
        )
    )

    dados_row_5 = [
        [
            f'<i>Tel. Resid.: </i><br/><b>{candidato.telefone or "-"}</b>',
            f'<i>Celular: </i><br/><b>{candidato.telefone2 or "-"}</b>',
            f"<i>E-mail: </i><br/><b>{candidato.email.lower()}</b>",
        ]
    ]
    documento.append(
        pdf.table(
            dados_row_5, a=["l", "l", "l"], w=[50, 45, 95], grid=1, zebra=0, fontSize=8
        )
    )

    dados_row_6 = [
        [
            f"<i>Endereço: </i><br/><b>{candidato.logradouro.upper()}</b>",
            f"<i>Número: </i><br/><b>{candidato.numero_endereco.upper()}</b>",
            f'<i>Complemento: </i><br/><b>{candidato.complemento_endereco or "-"}</b>',
        ]
    ]
    documento.append(
        pdf.table(dados_row_6, a=["l", "l", "l"], w=[95, 25, 70], grid=1, fontSize=8)
    )

    dados_row_7 = [
        [
            f"<i>Bairro: </i><br/><b>{candidato.bairro.upper()}</b>",
            f"<i>CEP: </i><br/><b>{candidato.cep}</b>",
            f"<i>Cidade: </i><br/><b>{candidato.municipio.upper()}</b>",
            f"<i>UF: </i><br/><b>{candidato.uf}</b><br/>",
        ]
    ]
    documento.append(
        pdf.table(
            dados_row_7,
            a=["l", "l", "l", "l"],
            w=[75, 20, 80, 15],
            grid=1,
            zebra=2,
            fontSize=8,
        )
    )

    documento.append(
        pdf.table(
            [["<b>DADOS SOCIOECONÔMICOS</b>"]], w=[190], grid=1, head=1, fontSize=8
        )
    )

    dados_row_8 = [
        [
            f"<i>Estado Civil: </i><br/><b>{caract.estado_civil}</b>",
            f"<i>Companhia domiciliar: </i><br/><b>{caract.companhia_domiciliar}</b>",
            f"<i>Nº de Membros da Família: </i><br/><b>{caract.qtd_pessoas_domicilio}</b>",
            f"<i>Renda Bruta Familiar: </i><br/><b>R$ {pdf.moeda_real_display(caract.renda_bruta_familiar)}</b>",
            f"<i>Renda Per Capita: </i><br/><b>R$ {pdf.moeda_real_display(caract.renda_per_capita)}</b>",
        ]
    ]
    documento.append(
        pdf.table(
            dados_row_8,
            a=["l", "l", "l", "l", "l"],
            w=[30, 50, 45, 35, 30],
            grid=1,
            zebra=0,
            fontSize=8,
        )
    )

    dados_row_9 = [
        [
            f"<i>Est. Civil do Pai: </i><br/><b>{caract.estado_civil_pai}</b>",
            f"<i>Pai falecido: </i><br/><b>{pdf.human_str(caract.pai_falecido)}</b>",
            f"<i>Est. Civil da Mãe: </i><br/><b>{caract.estado_civil_mae}</b>",
            f"<i>Mãe falecida: </i><br/><b>{pdf.human_str(caract.mae_falecida)}</b>",
            f"<i>Grau de Escolaridade: </i><br/><b>{caract.escolaridade}</b>",
        ]
    ]
    documento.append(
        pdf.table(
            dados_row_9,
            a=["l", "l", "l", "l", "l"],
            w=[30, 20, 30, 25, 85],
            grid=1,
            zebra=0,
            fontSize=8,
        )
    )

    if not curso.is_tecnico_integrado and caract.nome_escola_ensino_medio:
        escola_instit = caract.nome_escola_ensino_medio
        escola_ano = caract.ensino_medio_conclusao
        escola_tipo = caract.escola_ensino_medio
        escola_localizacao = caract.tipo_area_escola_ensino_medio
    elif caract.nome_escola_ensino_fundamental:
        escola_instit = caract.nome_escola_ensino_fundamental
        escola_ano = caract.ensino_fundamental_conclusao
        escola_tipo = caract.escola_ensino_fundamental
        escola_localizacao = caract.tipo_area_escola_ensino_fundamental
    else:
        escola_instit = "Não Informado"
        escola_ano = "Não Informado"
        escola_tipo = "Não Informado"

    dados_row_10 = [
        [
            f"<i>Instituição Educacional de Origem: </i><br/><b>{escola_instit}</b>",
            f"<i>Ano de Conclusão: </i><br/><b>{escola_ano}</b>",
            f"<i>Tipo de Escola: </i><br/><b>{escola_tipo} - {escola_localizacao}</b>",
        ]
    ]
    documento.append(
        pdf.table(
            dados_row_10,
            a=["l", "l", "l"],
            w=[100, 30, 60],
            grid=1,
            zebra=0,
            fontSize=8,
        )
    )
    documento.append(pdf.space(2))

    observacao = [
        [
            "<b>OBSERVAÇÃO:</b><br/>"
            "<i>O aluno, neste ato, fica ciente que, deverá manter atualizados seu endereço, telefones,"
            " e-mails e demais dados cadastrais, junto a esta Instituição de Ensino, sendo de sua"
            " responsabilidade os prejuízos decorrentes da não atualização destas informações.</i>"
        ]
    ]
    documento.append(
        pdf.table(observacao, a=["l"], w=[190], grid=1, zebra=0, fontSize=8)
    )

    declaracao = [
        [
            f"<b>DECLARAÇÃO: </b><br/>"
            f"<i>1. DECLARO, para fins de direito, não possuir existência de vínculo na condição de"
            f" estudante em outra Instituição de Ensino Superior Pública, conforme determina a Lei "
            f" nº 12.089, de 11 de novembro de 2009.</i><br/>"
            f"<i>2. DECLARO, para fins de direito, sob as penas da lei, que as informações e os "
            f" documentos que apresento para pré-matrícula no IFPB, relativa ao ano letivo de "
            f" {chamada.etapa.edicao.ano}, são fiéis à verdade e condizentes com a realidade dos "
            f" fatos. Fico ciente, portanto, que a falsidade desta declaração configura-se em crime "
            f" previsto no Código Penal Brasileiro e passível de apuração na forma da Lei.</i>"
        ]
    ]
    documento.append(
        pdf.table(declaracao, a=["l"], w=[190], grid=1, zebra=0, fontSize=8)
    )
    documento.append(pdf.space(7))

    assinatura = []
    assinatura.append(
        [
            "_________________________________________<br/>Assinatura do(a) Responsável<br/>",
            "_________________________________________<br/>Assinatura do(a) Candidato(a)",
        ]
    )
    assinatura.append(
        [
            f"CPF:________________________ Tel.: (____) _________________<br/>"
            f"Responsável pelo(a) aluno(a) <b>(se menor de idade ou por procuração)</b>",
            f'<br/>{cidade}, {datetime.now().strftime("%d/%m/%Y")}',
        ]
    )
    documento.append(
        pdf.table(assinatura, a=["c", "c"], w=[105, 85], grid=0, zebra=0, fontSize=8)
    )
    documento.append(pdf.space(1))

    # rodapé
    documento.append(
        pdf.para(
            "----------------------------------------------------------------------------------------"
            "------------------------------------------------------------------",
            alignment="center",
        )
    )
    dados_rodape = []
    edicao = chamada.etapa.edicao
    str_rodape = (
        f"<font size=12><b>Comprovante de Pré-Matrícula - "
        f"<i>Campus {curso.campus.nome}</i></b></font>"
        f"<br/><br/><i>Curso: </i><b>{nome_curso} - {curso.get_turno_display()}</b><br/>"
        f"<i>Aluno(a): </i><b>{candidato.nome.upper()}</b><br/>"
        f"<i>Ano/Período Letivo: </i><b>{edicao.ano}.{edicao.semestre}</b>"
    )
    image_path_rodape = os.path.join(
        settings.BASE_DIR, "templates", "publico", "img", "logo-ifpb-vertical.png"
    )
    image_rodape = pdf.Image(
        image_path_rodape, width=18.1 * pdf.mm, height=22.0 * pdf.mm
    )
    dados_rodape.append(
        [
            image_rodape,
            str_rodape,
            f"<br/><br/>_________________________<br/>"
            f"Funcionário(a)<br/>"
            f'{cidade}, {datetime.now().strftime("%d/%m/%Y")}',
        ]
    )
    documento.append(
        pdf.table(dados_rodape, a=["c", "l", "c"], w=[25, 115, 50], grid=0, fontSize=9)
    )

    if chamada.modalidade.is_cota_renda():
        documento.append(pdf.page_break())
        documento.extend(gerar_declaracao_renda(candidato, caract, cidade))

    if chamada.modalidade.is_cota_racial():
        documento.append(pdf.page_break())
        documento.extend(gerar_declaracao_ppi(candidato, cidade))

    return pdf.PdfReport(body=documento, pages_count=0).generate()


def gerar_declaracao_renda(candidato, caracterizacao, cidade):
    # Definições
    nome_candidato = candidato.nome.upper()
    renda = pdf.moeda_real_display(caracterizacao.renda_bruta_familiar)
    cidade_e_data = f'{cidade}, {datetime.now().strftime("%d de %B de %Y")}.'
    NR_ATIVIDADES = 3
    NR_TESTEMUNHAS = 2

    documento = []

    documento.append(pdf.space(10))
    documento.append(pdf.para("DECLARAÇÃO DE RENDA FAMILIAR", style="h1", align="c"))
    documento.append(pdf.space(10))
    texto_0 = (
        "Eu, ___________________________________________________________, CPF nº _____________________, "
        f"declaro que a renda familiar do aluno(a) {nome_candidato} é de R$ {renda} mensais, referente "
        "aos ganhos obtidos no trabalho de nossa família, em atividades de "
        "____________________________________________________________________, conforme abaixo discriminadas:"
    )
    documento.append(pdf.para(texto_0))
    documento.append(pdf.space(5))

    for count in range(1, NR_ATIVIDADES + 1):
        atividade = (
            f"Atividade {count}: ____________________________________________________________ <br/>"
            "Endereço do trabalho: Rua________________________________________ Nº ______ <br/>"
            "Bairro: ___________________________ Município: ___________________________."
        )
        documento.append(pdf.para(atividade))
        documento.append(pdf.space(3))

    texto_1 = (
        "Declaro ainda que, o valor acima apresentado é verdadeiro e estou ciente de que a omissão de "
        "informações ou a apresentação de dados ou documentos falsos e/ou divergentes implicam no "
        "cancelamento da matrícula no IFPB."
    )
    documento.append(pdf.para(texto_1))
    texto_2 = (
        "As informações constantes nesta declaração são de minha responsabilidade e, caso sejam inverídicas, "
        "responderei em conformidade com a legislação vigente."
    )
    documento.append(pdf.para(texto_2))

    documento.append(pdf.space(10))
    documento.append(pdf.para(cidade_e_data, align="r"))
    documento.append(pdf.space(10))
    documento.append(
        pdf.para(
            "___________________________________________<br/>Assinatura do(a) Declarante",
            align="c",
        )
    )

    documento.append(pdf.space(10))
    documento.append(pdf.para("Testemunhas:"))
    documento.append(pdf.space(5))
    for count in range(NR_TESTEMUNHAS):
        documento.append(
            pdf.para(
                "Nome ________________________________________________ CPF Nº ____________________"
            )
        )
        documento.append(pdf.space(5))

    return documento


def gerar_declaracao_ppi(candidato, cidade):
    nome_candidato = candidato.nome.upper()
    cidade_e_data = f'{cidade}, {datetime.now().strftime("%d de %B de %Y")}.'
    documento = []

    documento.append(pdf.space(15))
    documento.append(
        pdf.para(
            "DECLARAÇÃO DE PERTENCIMENTO AOS GRUPOS ÉTNICOS PRETO, PARDO OU INDÍGENA",
            style="h1",
            align="c",
        )
    )
    documento.append(pdf.space(25))
    texto_0 = (
        f"Eu, <b>{nome_candidato}</b>, inscrito(a) no CPF de número <b>{candidato.cpf}</b>, declaro, para "
        "os devidos fins de direito, que pertenço ao grupo étnico informado abaixo, sendo, portanto, "
        "detentor dos direitos abrigados pela Lei nº 12.711, de 29 de agosto de 2012."
    )
    documento.append(pdf.para(texto_0))
    documento.append(pdf.space(5))

    texto_1 = "Grupo étnico ao qual pertenço:"
    documento.append(pdf.para(texto_1))
    documento.append(pdf.space(5))

    documento.append(pdf.para("____ Preto"))
    documento.append(pdf.space(5))

    documento.append(pdf.para("____ Pardo"))
    documento.append(pdf.space(5))

    documento.append(pdf.para("____ Indígena"))
    documento.append(pdf.space(20))

    documento.append(pdf.para(cidade_e_data, align="r"))
    documento.append(pdf.space(15))
    documento.append(
        pdf.para(
            "___________________________________________<br/>Assinatura do(a) Declarante",
            align="c",
        )
    )

    return documento
