from django.conf.urls import url

from psct.views import relatorios as views

urlpatterns = [
    url("^relatorios/demanda/$", views.DemandaView.as_view(), name="demanda"),
    url("^relatorios/validacoes/$", views.AvaliacoesView.as_view(), name="avaliacoes"),
    url(
        "^relatorios/status_validacoes/$",
        views.StatusAvaliacoesView.as_view(),
        name="status_avaliacoes",
    ),
    url(
        "^relatorios/validadores/$", views.AvaliadoresView.as_view(), name="avaliadores"
    ),
    url(
        "^relatorios/ajustes_pontuacao/$",
        views.AjustesView.as_view(),
        name="ajustes_pontuacao",
    ),
    url("^dashboard/$", views.DashboardView.as_view(), name="dashboard"),
]
