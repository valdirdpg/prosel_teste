from datetime import date, timedelta

from django.apps import apps
from django_google_charts import charts

from psct.dashboard import queries
from psct.models import SituacaoAvaliacao

AvaliacaoAvaliador = apps.get_model("psct", "AvaliacaoAvaliador")


class InscricoesPorSituacao(charts.PieChart):
    chart_slug = "pizza_grafico"

    options = {
        "legend": {"position": "right"},
        "animation": {"startup": True, "duration": 300, "easing": "in"},
        "pieHole": 0.4,
        "curveType": "function",
        "chartArea": {"left": 10, "top": 10, "width": "90%", "height": "90%"},
    }

    columns = (("string", "Situação"), ("number", "Quantidade"))

    def __init__(self, edital=None, campus=None, curso=None):
        self.edital = edital
        self.campus = campus
        self.curso = curso

    def get_data(self):
        concluidas = queries.get_inscricoes_concluidas(
            self.edital, self.campus, self.curso
        ).count()
        nao_concluidas = queries.get_inscricoes_nao_concluidas(
            self.edital, self.campus, self.curso
        ).count()

        return (["Concluídas", concluidas], ["Não concluídas", nao_concluidas])


class AproveitamentoInscricoes(charts.PieChart):
    chart_slug = "aproveitamento_inscricoes"

    options = {
        "legend": {"position": "right"},
        "animation": {"startup": True, "duration": 300, "easing": "in"},
        "chartArea": {"left": 10, "top": 10, "width": "90%", "height": "90%"},
    }

    columns = (("string", "Situação"), ("number", "Quantidade"))

    def __init__(self, edital=None, campus=None, curso=None):
        self.edital = edital
        self.campus = campus
        self.curso = curso

    def get_data(self):
        indeferidas = queries.get_inscricoes_indeferidas(
            self.edital, self.campus, self.curso
        ).count()
        deferidas = queries.get_inscricoes_deferidas(
            self.edital, self.campus, self.curso
        ).count()

        return (["Deferidas", deferidas], ["Indeferidas", indeferidas])


class AndamentoRecurso(charts.BarChart):
    chart_slug = "andamento_recurso"

    options = {
        "isStacked": "percent",
        "bar": {"groupWidth": "30%"},
        "hAxis": {"minValue": 0, "ticks": [0, 0.25, 0.5, 0.75, 1]},
        "chartArea": {"left": 200, "width": "100%"},
        "animation": {"startup": True, "duration": 700, "easing": "in"},
        "legend": {"position": "top"},
    }

    columns = (
        ("string", "Nome"),
        ("number", "Não Avaliados"),
        ("number", "Avaliados"),
        ("number", "Homologados"),
    )

    def __init__(self, edital=None, campus=None, curso=None):
        self.edital = edital
        self.campus = campus
        self.curso = curso

    def get_data(self):
        query = queries.RecursoQuery(self.edital, self.campus, self.curso)
        situacoes_map = {
            "Não Avaliados": [
                query.COM_AVALIACAO_PENDENTE,
                query.AVALIADORES_INCOMPLETOS,
                query.COM_AVALIACAO_NAO_CONCLUIDA,
            ],
            "Avaliados": [query.AGUARDANDO_HOMOLOGADOR],
            "Homologados": [query.HOMOLOGADO],
        }

        dados = []
        fases = query.get_fases()
        for fase in fases:
            dados_fase = [str(fase)]
            for situacoes in situacoes_map.values():
                ids = []
                for situacao in situacoes:
                    ids.append(
                        query.filter_situacao(situacao, fase).values_list(
                            "id", flat=True
                        )
                    )
                total = len(list(set(ids)))
                dados_fase.append(total)
            dados.append(dados_fase)
        return dados


class AvaliacoesHomologacoesDiarias(charts.AreaChart):
    chart_slug = "avaliacoes_homologacoes_diarias"

    columns = (
        ("string", "Dia"),
        ("number", "Avaliações"),
        ("number", "Deferidas"),
        ("number", "Indeferidas"),
    )

    options = {
        "legend": {"position": "top"},
        "animation": {"startup": True, "duration": 400, "easing": "in"},
        "vAxis": {"minValue": 0, "textStyle": {"fontSize": 11, "color": "gray"}},
        "hAxis": {"textStyle": {"fontSize": 11, "color": "gray"}},
        "chartArea": {"left": 40, "top": 20, "width": "100%", "height": "70%"},
        "width": "100%",
    }

    def __init__(self, edital=None, campus=None, curso=None):
        self.edital = edital
        self.campus = campus
        self.curso = curso

    def get_data(self):
        params_avaliacao = {}
        params_deferidas = {"situacao": SituacaoAvaliacao.DEFERIDA.name}
        params_indeferidas = {"situacao": SituacaoAvaliacao.INDEFERIDA.name}
        if self.edital:
            params_avaliacao["inscricao__fase__edital"] = self.edital

        if self.campus:
            params_avaliacao["inscricao__curso__campus"] = self.campus

        if self.curso:
            params_avaliacao["inscricao__curso"] = self.curso

        data = []
        for dia in self.get_days():
            params_avaliacao["data_atualizacao__date"] = dia
            params_deferidas.update(params_avaliacao)
            params_indeferidas.update(params_avaliacao)

            avaliacoes = AvaliacaoAvaliador.objects.filter(**params_avaliacao).count()
            deferidas = AvaliacaoAvaliador.objects.filter(**params_deferidas).count()
            indeferidas = AvaliacaoAvaliador.objects.filter(
                **params_indeferidas
            ).count()
            data.append([dia.strftime("%d/%m"), avaliacoes, deferidas, indeferidas])
        data = list(reversed(data))
        return data

    def get_days(self):
        count = 0
        day = date.today()
        one_day = timedelta(days=1)
        while count < 15:
            if day.weekday() not in [5, 6]:
                yield day
                count += 1

            day -= one_day
