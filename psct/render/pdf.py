import abc

from base import pdf as b_pdf
from psct.render import base
from psct.render import register

pdf = register.FiletypeRender("pdf")


class PDFRender(base.SpecializedRender):
    def get_pdf_table(self, table, modalidade):
        if modalidade.is_ampla:
            return self.get_pdf_table_ampla(table)
        return self.get_pdf_table_cota(table)

    @abc.abstractmethod
    def get_pdf_table_ampla(self, table):
        pass

    @abc.abstractmethod
    def get_pdf_table_cota(self, table):
        pass

    def get_columns(self, modalidade):
        columns = self.render.get_columns(modalidade)
        return [f"<b>{c}</b>" for c in columns]

    def get_table(self, curso, modalidade):
        table = self.render.get_table(curso, modalidade)
        return self.get_pdf_table(table, modalidade)

    def paper(self):
        # Para usar orientação paisagem, inserir um '-' antes do formato
        return "A4"


@pdf.register(base.ResultadoDivulgacaoRenderer)
class ResultadoDivulgacaoRenderer(PDFRender):
    def get_pdf_table_ampla(self, table):
        return b_pdf.table(
            table,
            a=["c", "c", "l", "c"],
            w=[23, 18, 133, 12],
            head=1,
            grid=1,
            zebra=1,
            fontSize=8,
        )

    def get_pdf_table_cota(self, table):
        return self.get_pdf_table_ampla(table)


@pdf.register(base.ResultadoPreliminarDivulgacaoRenderer)
class ResultadoPreliminarDivulgacaoRenderer(ResultadoDivulgacaoRenderer):
    description = "Resultado Preliminar para divulgação"

    @property
    def title(self):
        return "RESULTADO PRELIMINAR"


@pdf.register(base.ListaControleRenderer)
class ListaControleRenderer(PDFRender):
    def get_pdf_table_ampla(self, table):
        return b_pdf.table(
            table,
            a=["c", "c", "l", "c"],
            w=[23, 18, 133, 12],
            head=1,
            grid=1,
            zebra=1,
            fontSize=8,
        )

    def get_pdf_table_cota(self, table):
        return b_pdf.table(
            table,
            a=["c", "c", "c", "l", "c"],
            w=[25, 25, 18, 105, 12],
            head=1,
            grid=1,
            zebra=1,
            fontSize=8,
        )


@pdf.register(base.ListaGeralRenderer)
class ListaGeralRenderer(PDFRender):
    def get_pdf_table_ampla(self, table):
        return b_pdf.table(
            table,
            a=["c", "c", "l", "c"],
            w=[23, 18, 100, 45],
            head=1,
            grid=1,
            zebra=1,
            fontSize=8,
        )

    def get_pdf_table_cota(self, table):
        return self.get_pdf_table_ampla(table)


@pdf.register(base.ResultadoDivulgacaoDDERenderer)
class ResultadoDivulgacaoDDERenderer(PDFRender):
    def get_pdf_table_ampla(self, table):
        return b_pdf.table(
            table,
            a=["c", "c", "c"],
            w=[70, 25, 100],
            head=1,
            grid=1,
            zebra=1,
            fontSize=8,
        )

    def get_pdf_table_cota(self, table):
        return self.get_pdf_table_ampla(table)


@pdf.register(base.ResultadoDivulgacaoCompletoRenderer)
class ResultadoDivulgacaoCompletoRenderer(PDFRender):
    def get_pdf_table_ampla(self, table):
        return b_pdf.table(
            table,
            a=["c", "c", "l", "c", "l", "l", "l"],
            w=[15, 18, 65, 12, 30, 50, 90],
            head=1,
            grid=1,
            zebra=1,
            fontSize=8,
        )

    def get_pdf_table_cota(self, table):
        return self.get_pdf_table_ampla(table)

    def paper(self):
        return "-A4"
