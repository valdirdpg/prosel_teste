import abc
import os
import tempfile
from datetime import datetime

import xlsxwriter
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from base import pdf
from cursos.models import Campus
from psct.models import inscricao as inscricao_models
from psct.render import register


class Driver(metaclass=abc.ABCMeta):
    filetype = None

    def __init__(self, resultado, render_id):
        self.resultado = resultado
        self.fase = self.resultado.fase
        render_class = register.get_renderer(render_id, self.filetype)
        self.render = render_class(self.resultado)
        self.files = []

    @abc.abstractmethod
    def run(self):
        pass

    def report(self, user):
        assunto = "[Portal do Estudante] {} - {} do {}".format(
            self.filetype.upper(), self.render.description, self.fase.edital
        )
        mensagem = render_to_string(
            "psct/mails/resultado_preliminar.html",
            dict(user=user, edital=self.fase.edital, render=self.render),
        )

        email = EmailMessage(
            assunto,
            mensagem,
            settings.EMAIL_FROM,
            [user.email],
            reply_to=[settings.EMAIL_REPLY_TO],
        )

        for a in self.files:
            email.attach_file(a)
        email.send()

        if settings.DEBUG:
            for filename in self.files:
                print(filename)


class PDFDriver(Driver):
    filetype = "pdf"

    def run(self):
        directory = tempfile.mkdtemp()
        for campus in Campus.objects.filter(
            cursonocampus__cursoselecao__processoinscricao__edital=self.fase.edital
        ).distinct():
            filename = os.path.join(directory, campus.sigla + ".pdf")
            with open(filename, "wb") as f:
                f.write(self.generate_file(campus))
            self.files.append(filename)

    def generate_file(self, campus):
        documento = []
        edital = self.fase.edital
        # cabecalho
        image_logo_path = os.path.join(
            settings.BASE_DIR, "templates", "publico", "img", "logo-ifba-new.jpg"
        )
        image_logo = pdf.Image(
            image_logo_path, width=49.6 * pdf.mm, height=13.0 * pdf.mm
        )
        str_cabecalho = (
            
             "PROCESSO SELETIVO PARA CURSOS TÉCNICOS - EDITAL Nº {}/{}<br/>".format(
                edital.numero, edital.ano
            )
            + f"<b>{self.render.title}</b>"
        )

        tbl_cabecalho = pdf.table(
            rows=[[image_logo, str_cabecalho]],
            a=["c", "c"],
            w=[40, 155],
            grid=0,
            fontSize=10,
        )
        documento.append(tbl_cabecalho)
        documento.append(pdf.space(10))

        campus_nome = f"<b>CAMPUS {campus.nome.upper()}</b>"
        documento.append(pdf.para(campus_nome, align="center"))

        documento.append(pdf.space(15))

        for curso in self.fase.edital.processo_inscricao.cursos.filter(campus=campus):

            curso_nome = "<b>CURSO {} - TURNO {}</b>".format(
                curso.curso.nome.upper(), curso.get_turno_display().upper()
            )
            documento.append(pdf.para(curso_nome, align="center"))
            documento.append(pdf.space(5))

            for modalidade in inscricao_models.Modalidade.objects.all():

                if not self.render.has_output(curso, modalidade):
                    continue

                documento.append(pdf.para(f"<b>{modalidade}</b>"))
                documento.append(pdf.space(5))
                documento.append(self.render.get_table(curso, modalidade))
                documento.append(pdf.space(5))

            documento.append(pdf.space(15))

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

        return pdf.PdfReport(
            body=documento, footer_args=rodape, pages_count=1, paper=self.render.paper()
        ).generate()


class XLSDriver(Driver):
    filetype = "xls"

    def run(self):
        directory = tempfile.mkdtemp()
        for campus in Campus.objects.filter(
            cursonocampus__processoinscricao__edital=self.fase.edital
        ).distinct():
            self.files.append(self.generate_file(campus, directory))

    def generate_file(self, campus, directory):
        filename = os.path.join(directory, campus.sigla + ".xls")
        workbook = xlsxwriter.Workbook(filename)

        for curso in self.fase.edital.processo_inscricao.cursos.filter(campus=campus):

            curso_nome = "{}-{}".format(
                curso.curso.nome.upper(), curso.get_turno_display().upper()
            )
            curso_nome = curso_nome[:30]  # tamanho limite do nome de uma planilha

            sheet = workbook.add_worksheet(curso_nome)
            line_counter = 0

            for modalidade in inscricao_models.Modalidade.objects.all():

                if not self.render.has_output(curso, modalidade):
                    continue

                sheet.write(line_counter, 0, str(modalidade))
                line_counter += 1

                table = self.render.get_table(curso, modalidade)
                for row in table:
                    sheet.write_row(line_counter, 0, row)
                    line_counter += 1

                line_counter += 2

        return filename


def list_drivers():
    options = set()
    items = {Driver}
    while items:
        cls = items.pop()
        options.add(cls)
        for subcls in cls.__subclasses__():
            items.add(subcls)
    options.remove(Driver)
    return list(options)


def get_driver(filetype):
    return [d for d in list_drivers() if d.filetype == filetype][0]


def get_choices():
    drivers = list_drivers()
    choices = [(d.filetype, d.filetype.upper()) for d in drivers]
    return [("", "---------")] + sorted(choices, key=lambda x: x[1])
