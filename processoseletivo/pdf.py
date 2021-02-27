import os
import tempfile
from datetime import datetime

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.text import slugify

from base import pdf
from cursos.models import Campus
from processoseletivo import models
from processoseletivo.choices import Status


def imprimir_lista_analise_documental(etapa, queryset_chamadas, campus=None):
    """
    - Lista da situação documental dos candidatos da chamada - mostra a situação de todos os candidatos, inclusive os que
    nao entregaram a documentação
    - Divide por grupo na exibição da lista
    """

    documento = []

    # cabecalho
    image_path = os.path.join(
        settings.BASE_DIR, "templates", "publico", "img", "logo-ifba-new.jpg"
    )
    image = pdf.Image(image_path, width=49.6 * pdf.mm, height=13.0 * pdf.mm)
    if campus:
        str_cabecalho = "<i>{}</i><br/><i>{} - Campus {}</i><br/>".format(
            etapa.edicao, etapa.nome, campus
        )
    else:
        str_cabecalho = f"<i>{etapa.edicao}</i><br/><i>{etapa.nome}</i><br/>"
    str_cabecalho += (
        "<b>Lista de candidatos com status de acordo com a análise da documentação</b>"
    )
    tbl_cabechalho = pdf.table(
        rows=[[image, str_cabecalho]], a=["c", "c"], w=[50, 135], grid=0, fontSize=12
    )
    documento.append(tbl_cabechalho)
    documento.append(pdf.space(1))

    # Listagem de sitaucao documental
    documento.append(
        pdf.para(
            "<b>Atenção:</b> Verificar situação da documentação. Candidatos <b>indeferidos</b> têm direito a entrar com recurso <br/>"
            " Obs. Listagem em ordem alfabética por Curso e Modalidade e ordem de classificação por Candidatos.",
            style="Italic",
            size="8",
        )
    )
    documento.append(pdf.space(1))

    for c in queryset_chamadas:
        lista_chamadas = [
            [
                "<b>Curso:</b> {} <br/> <b>Modalidade:</b> {}".format(
                    c.curso.nome, c.modalidade.nome
                )
            ]
        ]
        tbl_chamadas = pdf.table(
            lista_chamadas, a=["l"], w=[188], grid=1, zebra=0, fontSize=8
        )
        documento.append(tbl_chamadas)

        lista_deferido = []
        lista_indeferido = []
        lista_nao_entregue = []

        qtd_deferido = qtd_indeferido = qtd_nao_entregue = 0

        inscricoes = c.inscricoes.all()

        for inscricao in inscricoes:
            analise = models.AnaliseDocumental.objects.filter(
                confirmacao_interesse__inscricao=inscricao
            ).first()

            qtd_nao_entregue += 1
            if analise:
                if analise.situacao_final:
                    qtd_deferido += 1
                    texto = "DOCUMENTAÇÃO VÁLIDA"
                    lista_deferido.append(
                        [
                            str(qtd_deferido),
                            str(inscricao.candidato),
                            texto,
                            analise.observacao,
                        ]
                    )
                else:
                    qtd_indeferido += 1
                    texto = "DOCUMENTAÇÃO INVÁLIDA"
                    lista_indeferido.append(
                        [
                            str(qtd_indeferido),
                            str(inscricao.candidato),
                            texto,
                            analise.observacao,
                        ]
                    )
            else:
                texto = "DOCUMENTAÇÃO NÃO ENTREGUE"
                obs = "DOCUMENTAÇÃO NÃO ENTREGUE"
                lista_nao_entregue.append(
                    [
                        str(qtd_nao_entregue),
                        str(inscricao.candidato),
                        texto,
                        "DOCUMENTAÇÃO NÃO ENTREGUE",
                    ]
                )

        if not lista_deferido:
            tbl_listagem_deferido = pdf.table(
                [["<b>Nenhum candidato com documentação deferida</b>"]],
                a=["c"],
                w=[188],
                grid=1,
                zebra=1,
                fontSize=8,
            )
        else:
            tabela_lista = pdf.table(
                [["<b>Candidatos com documentação deferida</b>"]],
                a=["c"],
                w=[188],
                grid=1,
                zebra=1,
                fontSize=8,
            )
            documento.append(tabela_lista)

            tbl_listagem_deferido = pdf.table(
                lista_deferido,
                a=["c", "l", "c", "c"],
                w=[7, 70, 43, 68],
                grid=1,
                zebra=1,
                fontSize=8,
            )

        documento.append(tbl_listagem_deferido)
        documento.append(pdf.space(2))

        if not lista_indeferido:
            tbl_listagem_indeferido = pdf.table(
                [["<b>Nenhum candidato com documentação indeferida</b>"]],
                a=["c"],
                w=[188],
                grid=1,
                zebra=1,
                fontSize=8,
            )
        else:
            tabela_lista = pdf.table(
                [["<b>Candidatos com documentação indeferida</b>"]],
                a=["c"],
                w=[188],
                grid=1,
                zebra=0,
                fontSize=8,
                title_red=True,
            )
            documento.append(tabela_lista)

            tbl_listagem_indeferido = pdf.table(
                lista_indeferido,
                a=["c", "l", "c", "c"],
                w=[7, 70, 43, 68],
                grid=1,
                zebra=1,
                fontSize=8,
            )

        documento.append(tbl_listagem_indeferido)
        documento.append(pdf.space(2))

    dados_rodape = []
    str_rodape = (
        "________________________________________________________________________________________<br/><br/>"
        "INSTITUTO FEDERAL DE EDUCAÇÃO, CIÊNCIA E TECNOLOGIA DA PARAÍBA - IFPB<br/>"
        "Campus {}<br/>"
        "Coordenação de Controle Acadêmico".format(campus or etapa.campus)
    )
    dados_rodape.append([f"{str_rodape} - {datetime.now().strftime('%d/%m/%Y')}"])
    tbl_rodape = pdf.table(dados_rodape, a=["c"], w=[188], grid=0, fontSize=9)
    documento.append(tbl_rodape)

    return pdf.PdfReport(body=documento, pages_count=0).generate()


#
# Listagem final da expondo a situação de cada candidato - DEFERIDO, INDEFERIDO, EXCEDENTE
#
class RelatorioFinalEtapa:
    status = None
    title = ""
    prefix = "resultado_final"
    ordering_lista = None
    ordering_msg = "Listagem em ordem de classificação por Curso, Turno e Modalidade."

    def __init__(self, etapa, user):
        self.etapa = etapa
        self.etapa_sistemica = not etapa.campus
        self.user = user
        self.files = []

    def get_table(self, chamada):
        raise NotImplementedError(
            "É necessário implementar o método get_table com a tabela a ser gerada."
        )

    def get_lista(self, chamada):
        if not self.ordering_lista:
            order_params = ["inscricao__desempenho__classificacao"]
        elif isinstance(self.ordering_lista, str):
            order_params = list(self.ordering_lista)
        else:
            order_params = self.ordering_lista
        return models.Resultado.objects.filter(
            etapa=self.etapa, inscricao__in=chamada.inscricoes.all(), status=self.status
        ).order_by(*order_params)

    def has_output(self, chamada):
        return models.Resultado.objects.filter(
            etapa=self.etapa, inscricao__in=chamada.inscricoes.all(), status=self.status
        ).exists()

    def generate_files(self):
        directory = tempfile.mkdtemp()

        if not self.etapa_sistemica:
            filename = os.path.join(directory, self.prefix + ".pdf")
            with open(filename, "wb") as f:
                f.write(self._generate_file())
            self.files.append(filename)
        else:
            for campus in Campus.objects.filter(
                cursonocampus__chamada__etapa=self.etapa
            ).distinct():
                name = f"{self.prefix}_campus_{campus.sigla.lower()}.pdf"
                filename = os.path.join(directory, name)

                with open(filename, "wb") as f:
                    f.write(self._generate_file(campus))

                self.files.append(filename)
        self.report()

    def _generate_file(self, campus=None):
        documento = []
        etapa = self.etapa

        # cabecalho
        image_path = os.path.join(
            settings.BASE_DIR, "templates", "publico", "img", "logo-ifba-new.jpg"
        )
        image = pdf.Image(image_path, width=49.6 * pdf.mm, height=13.0 * pdf.mm)
        if campus:
            str_cabecalho = "<i>{}</i><br/><i>{} - Campus {}</i><br/>".format(
                etapa.edicao, etapa.nome, campus
            )
        else:
            str_cabecalho = f"<i>{etapa.edicao}</i><br/><i>{etapa.nome}</i><br/>"
        str_cabecalho += f"<br/><b>Resultado Final - {self.title}</b>"

        tbl_cabecalho = pdf.table(
            rows=[[image, str_cabecalho]],
            a=["c", "c"],
            w=[50, 135],
            grid=0,
            fontSize=12,
        )
        documento.append(tbl_cabecalho)
        documento.append(pdf.space(5))

        # Listagem de situacao documental
        documento.append(
            pdf.para(f"Obs. {self.ordering_msg}", style="Italic", size="8")
        )
        documento.append(pdf.space(1))

        order_by_params = [
            "curso__campus__nome",
            "curso__curso__nome",
            "curso__turno",
            "modalidade",
        ]
        if campus:
            chamadas = etapa.chamadas.filter(curso__campus=campus)
        else:
            chamadas = etapa.chamadas

        for chamada in chamadas.order_by(*order_by_params):
            if self.has_output(chamada) or self.status == Status.DEFERIDO.value:
                modalidade = chamada.modalidade.nome
                if chamada.curso.is_tecnico:
                    modalidade = modalidade.replace(
                        "ensino médio", "ensino fundamental"
                    )
                lista_chamadas = [
                    [
                        f"<b>Curso:</b> {chamada.curso.nome} ({chamada.curso.get_formacao_display()})"
                        f" - <b>Turno:</b> {chamada.curso.get_turno_display()}<br/>"
                        f"<b>Modalidade:</b> {modalidade}"
                    ]
                ]
                documento.append(pdf.table(lista_chamadas, a=["l"], w=[188]))
                documento.append(self.get_table(chamada))
                documento.append(pdf.space(5))
            else:
                continue

        # rodapé
        str_rodape = (
            "________________________________________________________________________________________"
            "<br/>INSTITUTO FEDERAL DE EDUCAÇÃO, CIÊNCIA E TECNOLOGIA DA PARAÍBA - IFPB"
            "<br/>Campus {}"
            "<br/>Coordenação de Controle Acadêmico".format(campus or etapa.campus)
        )
        documento.append(pdf.para(str_rodape, align="center"))
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

        return pdf.PdfReport(
            body=documento, footer_args=rodape, pages_count=0
        ).generate()

    def report(self):
        assunto = f"[Portal do Estudante] {self.title} da {self.etapa}"
        mensagem = render_to_string(
            "processoseletivo/mails/resultado_final.html",
            dict(user=self.user, etapa=self.etapa),
        )

        email = EmailMessage(
            assunto,
            mensagem,
            settings.EMAIL_FROM,
            [self.user.email],
            reply_to=[settings.EMAIL_REPLY_TO],
        )

        for f in self.files:
            email.attach_file(f)
            if settings.DEBUG:
                print(f)
        email.send()


class RelatorioFinalDeferidos(RelatorioFinalEtapa):
    status = Status.DEFERIDO.value
    title = "Lista de Candidatos Deferidos"
    prefix = "resultado_final_deferidos"
    ordering_lista = ["inscricao__desempenho__classificacao"]
    ordering_msg = "Listagem em ordem de classificação por Curso, Turno e Modalidade."

    def format_row(self, qs):
        result = [["Classif.", "Candidato(a)"]]
        for row in qs:
            result.append([row.inscricao.desempenho.classificacao, row])
        return result

    def get_table(self, chamada):
        if self.has_output(chamada):
            return pdf.table(
                self.format_row(self.get_lista(chamada)),
                a=["c", "l"],
                w=[15, 173],
                head=1,
                zebra=1,
            )
        return pdf.table(
            [["<b>Não há candidatos deferidos para esta modalidade e curso.</b>"]],
            a=["l"],
            w=[188],
            grid=0,
        )


class RelatorioFinalIndeferidos(RelatorioFinalEtapa):
    status = Status.INDEFERIDO.value
    title = "Lista de Candidatos Indeferidos"
    prefix = "resultado_final_indeferidos"

    def format_row(self, qs):
        result = [["Candidato", "Justificativa do Indeferimento"]]
        for row in qs:
            result.append([row.inscricao.candidato, row.observacao])
        return result

    def get_table(self, chamada):
        if self.has_output(chamada):
            return pdf.table(
                self.format_row(self.get_lista(chamada)),
                a=["l", "l"],
                w=[90, 98],
                head=1,
                zebra=1,
            )
        return pdf.table(
            [["<b>Nenhum candidato indeferido</b>"]], a=["c"], w=[188], grid=0
        )


class RelatorioFinalExcedentes(RelatorioFinalEtapa):
    status = Status.EXCEDENTE.value
    title = "Lista de Candidatos Excedentes"
    prefix = "resultado_final_excedentes"
    ordering_lista = ["inscricao__desempenho__classificacao"]
    ordering_msg = "Listagem em ordem de classificação por Curso, Turno e Modalidade."

    def format_row(self, qs):
        result = [["Classif.", "Candidato(a)"]]
        for row in qs:
            result.append([row.inscricao.desempenho.classificacao, row])
        return result

    def get_table(self, chamada):
        if self.has_output(chamada):
            return pdf.table(
                self.format_row(self.get_lista(chamada)),
                a=["c", "l"],
                w=[15, 173],
                head=1,
                zebra=1,
            )
        return pdf.table(
            [["<b>Nenhum candidato excedente</b>"]], a=["c"], w=[188], grid=0
        )


class RelatorioConvocadosPorCota:
    title = "Lista de Convocados por Cota"
    prefix = "lista-convocados"
    ordering_lista = ["desempenho__classificacao"]

    def __init__(self, etapa, user):
        self.etapa = etapa
        self.etapa_sistemica = not etapa.campus
        self.user = user
        self.files = []

    def format_row(self, qs):
        result = [["Classif. Geral", "Candidato(a)", "Nota", "Outra convocação?"]]
        for row in qs:
            inscricao_outra_chamada = row.get_inscricao_outra_chamada(self.etapa)
            if inscricao_outra_chamada:
                outra_convocacao = str(inscricao_outra_chamada.modalidade)
            else:
                outra_convocacao = ""
            result.append(
                [
                    row.desempenho.classificacao,
                    row.candidato,
                    row.desempenho.nota_geral,
                    outra_convocacao,
                ]
            )
        return result

    def get_lista(self, chamada):
        return chamada.inscricoes.all().order_by(*self.ordering_lista)

    def get_table(self, chamada):
        if self.has_output(chamada):
            return pdf.table(
                self.format_row(self.get_lista(chamada)),
                a=["c", "l", "c", "c"],
                w=[20, 80, 20, 50],
                head=1,
            )
        return pdf.table(
            [["<b>Não há candidatos convocados para esta modalidade e curso.</b>"]],
            a=["l"],
            w=[170],
        )

    def has_output(self, chamada):
        return chamada.inscricoes.exists()

    def generate_files(self):
        directory = tempfile.mkdtemp()

        if not self.etapa_sistemica:
            filename = os.path.join(directory, f"{self.prefix}.pdf")
            with open(filename, "wb") as f:
                f.write(self._generate_file())
            self.files.append(filename)
        else:
            for campus in Campus.objects.filter(
                cursonocampus__chamada__etapa=self.etapa
            ).distinct():
                filename = os.path.join(
                    directory, f"{self.prefix}-campus-{campus.sigla.lower()}.pdf"
                )
                with open(filename, "wb") as f:
                    f.write(self._generate_file(campus))
                self.files.append(filename)
        self.report()

    def _generate_file(self, campus=None):
        documento = []
        etapa = self.etapa

        # cabecalho
        image_path = os.path.join(
            settings.BASE_DIR, "templates", "publico", "img", "logo-ifba-new.jpg"
        )
        image = pdf.Image(image_path, width=49.6 * pdf.mm, height=13.0 * pdf.mm)
        if campus:
            str_cabecalho = (
                f"<i>{etapa.edicao}</i><br/><i>{etapa.nome} - Campus {campus}</i><br/>"
            )
        else:
            str_cabecalho = f"<i>{etapa.edicao}</i><br/><i>{etapa.nome}</i><br/>"
        str_cabecalho += f"<b>{self.title}</b>"

        cabecalho = {
            "height": 17,
            "story": [
                pdf.table(
                    rows=[[image, str_cabecalho]],
                    a=["c", "c"],
                    w=[50, 135],
                    grid=0,
                    fontSize=11,
                )
            ],
        }

        if campus:
            chamadas = etapa.chamadas.filter(curso__campus=campus)
        else:
            chamadas = etapa.chamadas
        order_by_params = [
            "curso__campus__nome",
            "curso__curso__nome",
            "curso__turno",
            "modalidade",
        ]
        curso_atual = ""
        primeira_pagina = True
        for chamada in chamadas.order_by(*order_by_params):
            if self.has_output(chamada):
                if curso_atual != chamada.curso:
                    if not primeira_pagina:
                        documento.append(pdf.page_break())
                    else:
                        primeira_pagina = False

                    curso_atual = chamada.curso
                    str_curso = (
                        f"<b>Curso:</b> {chamada.curso.nome} "
                        f"({chamada.curso.get_formacao_display()})"
                        f" - <b>Turno:</b> {chamada.curso.get_turno_display()}"
                    )
                    documento.append(pdf.para(str_curso, align="center"))
                    documento.append(pdf.space(5))

                lista_chamadas = [[f"<b>Modalidade:</b> {chamada.modalidade}"]]
                documento.append(
                    pdf.table(lista_chamadas, a=["l"], w=[170], fontSize=10)
                )
                documento.append(self.get_table(chamada))
                documento.append(pdf.space(5))
            else:
                continue

        return pdf.PdfReport(
            body=documento, header_args=cabecalho, pages_count=0
        ).generate()

    def report(self):
        assunto = f"[Portal do Estudante] {self.title} da {self.etapa}"
        mensagem = render_to_string(
            "processoseletivo/mails/generic.html",
            dict(
                user=self.user,
                corpo=(
                    "Conforme solicitado através do Portal do Estudante, segue em anexo o(s) "
                    f"arquivo(s) PDF(s) contendo a listagem de candidatos por cota do {self.etapa}."
                ),
            ),
        )

        email = EmailMessage(
            assunto,
            mensagem,
            settings.EMAIL_FROM,
            [self.user.email],
            reply_to=[settings.EMAIL_REPLY_TO],
        )

        for f in self.files:
            email.attach_file(f)
            if settings.DEBUG:
                print(f)
        email.send()


def verificar_documento_e_recurso(
    inscricao, vagas_preenchidas, vagas, etapa, excedente=False
):
    analise = models.AnaliseDocumental.objects.filter(
        confirmacao_interesse__inscricao=inscricao
    ).first()

    if not excedente:
        if vagas_preenchidas < vagas:
            return verificar_status(
                analise,
                etapa,
                Status.DEFERIDO.value,
                "CANDIDATO APTO A REALIZAR MATRÍCULA",
            )
        else:
            return "VERIFICAR", "VERIFICAR"
    else:
        return verificar_status(
            analise, etapa, Status.EXCEDENTE.value, "CANDIDATO NA LISTA DE ESPERA"
        )


def verificar_status(analise, etapa, status, observacao):
    if analise:
        inscricao = analise.confirmacao_interesse.inscricao
        if analise.situacao_final:
            if status == Status.DEFERIDO.value:
                if not models.Matricula.objects.filter(
                    inscricao=inscricao, etapa=etapa
                ).exists():
                    inscricao.matricular(etapa)

            cadastrar_resultado_preliminar(inscricao, etapa, status, observacao)
            return status, observacao
        else:
            recurso = models.Recurso.objects.filter(analise_documental=analise).first()
            if recurso:
                if recurso.status_recurso == Status.DEFERIDO.value:
                    if status == Status.DEFERIDO.value:
                        if not models.Matricula.objects.filter(
                            inscricao=inscricao, etapa=etapa
                        ).exists():
                            inscricao.matricular(etapa)

                    cadastrar_resultado_preliminar(inscricao, etapa, status, observacao)
                    return status, observacao
                else:
                    cadastrar_resultado_preliminar(
                        inscricao,
                        etapa,
                        Status.INDEFERIDO.value,
                        "RECURSO INDEFERIDO - " + recurso.justificativa.upper(),
                    )
                    return (
                        Status.INDEFERIDO.value,
                        "RECURSO INDEFERIDO - " + recurso.justificativa.upper(),
                    )
            else:
                # recurso nao enviado
                cadastrar_resultado_preliminar(
                    inscricao,
                    etapa,
                    Status.INDEFERIDO.value,
                    "DOCUMENTAÇÃO INVÁLIDA - " + analise.observacao.upper(),
                )
                return (
                    Status.INDEFERIDO.value,
                    "DOCUMENTAÇÃO INVÁLIDA - " + analise.observacao.upper(),
                )
    else:
        return Status.INDEFERIDO.value, "DOCUMENTAÇÃO NÃO ENTREGUE"


def cadastrar_resultado_preliminar(inscricao, etapa, status, obs):
    defaults = dict(status=status, observacao=obs)
    models.Resultado.objects.update_or_create(
        defaults=defaults, inscricao=inscricao, etapa=etapa
    )


#
# Gera os formulários de análise documental dos candidatos de uma chamada.
#
class FormulariosAnaliseDocumental:
    def __init__(self, chamada, user):
        self.chamada = chamada
        self.modalidade = chamada.modalidade
        self.curso = chamada.curso
        self.campus = self.curso.campus
        self.user = user
        self.files = []

    def queryset(self):
        return self.chamada.inscricoes.filter(
            confirmacaointeresse__isnull=False
        ).distinct()

    def generate_files(self):
        name = f"forms_analise_{slugify(self.modalidade)}_{slugify(self.curso)}.pdf"
        filename = os.path.join(tempfile.mkdtemp(), name)

        documento = []
        for inscricao in self.queryset():
            if inscricao != self.queryset().first():
                documento.append(pdf.page_break())
            documento.extend(self._generate_file(inscricao))

        if documento:
            with open(filename, "wb") as f:
                f.write(pdf.PdfReport(body=documento, pages_count=0).generate())
            self.files.append(filename)

        self.report()

    def _generate_file(self, inscricao):
        documento = []

        tipos = models.TipoAnalise.objects.filter(modalidade=self.modalidade)

        image_path = os.path.join(
            settings.BASE_DIR, "templates", "publico", "img", "logo-ifba-new.jpg"
        )
        image = pdf.Image(image_path, width=49.6 * pdf.mm, height=13.0 * pdf.mm)
        str_cabecalho = f"<i>Campus: </i><i>{self.campus.nome}</i>"

        tbl_cabechalho = pdf.table(
            rows=[[image, str_cabecalho]],
            a=["r", "l"],
            w=[118, 70],
            grid=0,
            fontSize=10,
        )
        documento.append(tbl_cabechalho)
        documento.append(pdf.space(5))

        tbl_dados_vaga = pdf.table(
            [["<b>ANÁLISE DOCUMENTAL DE PRÉ-MATRÍCULA PARTICIPANTE DE COTA</b>"]],
            w=[195],
            grid=1,
            head=1,
            fontSize=8,
        )
        documento.append(tbl_dados_vaga)

        dados_vaga = []
        dados_vaga.append(
            [
                f"<i>Candidato: </i><b>{inscricao.candidato.pessoa.nome.upper()}</b>",
                f"<i>Curso: </i><b>{self.curso.nome.upper()} ({self.curso.get_formacao_display()})</b>",
            ]
        )
        tbl_dados_vaga = pdf.table(
            dados_vaga, a=["l", "l"], w=[100, 95], grid=1, fontSize=8
        )
        documento.append(tbl_dados_vaga)
        documento.append(pdf.space(5))
        item = 0

        contador = 0

        for tipo in tipos:
            dados = []
            if tipo.nome == "DOCUMENTAÇÃO BÁSICA":
                tbl_dados = pdf.table(
                    [["<b>DOCUMENTAÇÃO BÁSICA</b>"]],
                    w=[195],
                    grid=1,
                    head=1,
                    fontSize=8,
                )
                documento.append(tbl_dados)
                lista = tipo.descricao.split(";")
                lista_itens = []
                d = dict()
                for l in lista:
                    lista_itens.append(l)
                    contador += 1
                    if (contador % 4) == 0:
                        d[item] = lista_itens
                        item += 1
                        lista_itens = []

                d[item] = lista_itens

                for k in d.keys():
                    texto = []
                    contador = 0
                    for i in d[k]:
                        texto.extend([f"<b> (  ) {i}</b>"])
                        contador += 1

                    for y in range(len(d[k]), 4):
                        texto.extend(["<b></b>"])
                    dados.append(texto)

                tbl_dados_alunos = pdf.table(
                    dados,
                    a=["l", "l", "l", "l"],
                    w=[45, 50, 50, 50],
                    grid=0,
                    zebra=0,
                    fontSize=6,
                )
                documento.append(tbl_dados_alunos)
            else:
                analise = [
                    [
                        f"<b>{tipo.nome} [SETOR - {tipo.setor_responsavel}]</b>",
                        "<b>SITUAÇÃO</b>",
                    ]
                ]
                tbl_dados_vaga = pdf.table(
                    analise, a=["l", "l"], w=[150, 45], grid=1, head=1, fontSize=8
                )
                documento.append(tbl_dados_vaga)
                dados.append(
                    [
                        f"{tipo.descricao}",
                        "( ) ATENDE<br/>( ) NÃO ATENDE<br/><br/>___/ ___/ ______",
                    ]
                )
                dados.append(
                    [
                        "<b>Observação: </b>",
                        "<br/>___________________________<br/>Assinatura com carimbo<br/>",
                    ]
                )
                tbl_dados_alunos = pdf.table(
                    dados, a=["l", "l"], w=[150, 45], grid=1, zebra=0, fontSize=7
                )
                documento.append(tbl_dados_alunos)
            documento.append(pdf.space(5))

        tbl_sit_final = pdf.table(
            [["<b>SITUAÇÃO FINAL DA PRÉ-MATRÍCULA</b>"]],
            w=[195],
            grid=1,
            head=1,
            fontSize=8,
        )
        documento.append(tbl_sit_final)

        dados = [
            [
                "<b><br/>Diante do exposto acima a pré-matrícula se apresenta: ( ) DEFERIDA ( ) INDEFERIDA<br/><br/></b>"
            ]
        ]
        tbl_dados = pdf.table(dados, a=["c"], w=[195], grid=1, zebra=0, fontSize=7)
        documento.append(tbl_dados)

        dados = []
        dados.append(
            ["<br/><br/>___________________________, _____/ _____/ _________<br/><br/>"]
        )
        dados.append(["_______________________________________________________"])
        dados.append(["Coordenação de Controle Acadêmico"])
        tbl_dados = pdf.table(dados, a=["c"], w=[195], grid=0, zebra=0, fontSize=7)
        documento.append(tbl_dados)

        return documento

    def report(self):
        assunto = f"[Portal do Estudante] Formulários de Análises Documentais - {self.chamada.etapa}"
        mensagem = render_to_string(
            "processoseletivo/mails/formularios_analise_documental.html",
            dict(user=self.user, chamada=self.chamada),
        )

        email = EmailMessage(
            assunto,
            mensagem,
            settings.EMAIL_FROM,
            [self.user.email],
            reply_to=[settings.EMAIL_REPLY_TO],
        )

        for f in self.files:
            email.attach_file(f)
            if settings.DEBUG:
                print(f)
        email.send()


class FormularioAnaliseDocumental:
    def __init__(self, avaliacao):
        self.avaliacao = avaliacao
        self.tipo = avaliacao.tipo_analise
        self.inscricao = avaliacao.analise_documental.confirmacao_interesse.inscricao
        self.chamada = self.inscricao.chamada
        self.modalidade = self.chamada.modalidade
        self.curso = self.chamada.curso
        self.campus = self.curso.campus

    def story(self):
        documento = []

        image_path = os.path.join(
            settings.BASE_DIR, "templates", "publico", "img", "logo-ifba-new.jpg"
        )
        image = pdf.Image(image_path, width=49.6 * pdf.mm, height=13.0 * pdf.mm)
        documento.append(image)
        documento.append(
            pdf.para(
                "ANÁLISE DOCUMENTAL DE PRÉ-MATRÍCULA PARTICIPANTE DE COTA",
                "h2",
                align="c",
            )
        )
        documento.append(pdf.para(f"Campus: {self.curso.campus.nome}", "h3", align="c"))
        documento.append(pdf.space(10))

        documento.append(
            pdf.para(
                f"{self.tipo.nome} - Setor Responsável: {self.tipo.setor_responsavel}",
                "h4",
                align="l",
            )
        )
        documento.append(pdf.para(f"<font size=8>{self.tipo.descricao}</font>"))
        documento.append(pdf.space(10))

        dados_vaga = []
        status = ""
        if not self.avaliacao.situacao:
            status = "Não "
        dados_vaga.append(
            [
                "<i>Candidato(a): </i>",
                f"<b>{self.inscricao.candidato.pessoa.nome.upper()}</b>",
            ]
        )
        dados_vaga.append(
            [
                "<i>Curso: </i>",
                f"<b>{self.curso.nome.upper()} ({self.curso.get_formacao_display()})</b>",
            ]
        )
        dados_vaga.append(["<i>Situação: </i>", f"<b>{status}Atende</b>"])
        dados_vaga.append(
            [
                "<i>Observações: </i>",
                f'<b>{self.avaliacao.observacao or "Não houveram"}</b>',
            ]
        )
        tbl_dados_vaga = pdf.table(
            dados_vaga, a=["l", "l"], w=[30, 156], grid=0, fontSize=10
        )
        documento.append(tbl_dados_vaga)
        documento.append(pdf.space(15))

        documento.append(
            pdf.para("___________________________, _____/ _____/ _________", align="c")
        )
        documento.append(pdf.para("Responsável pela avaliação", align="c"))

        return documento
