from django.conf.urls import url

from psct.views import resultado as views

urlpatterns = [
    url(
        r"^resultado/(?P<fase_pk>[\d]+)/resultado_preliminar/$",
        views.ResultadoPreliminarView.as_view(),
        name="resultado_preliminar_psct",
    ),
    url(
        r"^resultado/(?P<resultado_pk>[\d]+)/resultado_file/$",
        views.ResultadoFileView.as_view(),
        name="resultado_file_psct",
    ),
    url(
        r"^resultado/(?P<pk>[\d]+)/homologar_resultado_preliminar/$",
        views.HomologarResultadoPreliminarView.as_view(),
        name="homologar_resultado_preliminar_psct",
    ),
    url(
        r"^resultado/(?P<pk>[\d]+)/remover_homologacao_resultado_preliminar/$",
        views.RemoverHomologacaoResultadoPreliminarView.as_view(),
        name="remover_homologacao_resultado_preliminar_psct",
    ),
    url(
        r"^resultado/(?P<pk>[\d]+)/add/$",
        views.CreateResultadoView.as_view(),
        name="add_resultado_psct",
    ),
    url(
        r"^resultado/(?P<pk>[\d]+)/delete/$",
        views.DeleteResultadoView.as_view(),
        name="delete_resultado_psct",
    ),
    url(
        r"^resultado/inscricao/(?P<pk>[\d]+)/$",
        views.ResultadoInscricaoView.as_view(),
        name="view_resultado_inscricao_psct",
    ),
    url(
        r"^resultado/vagas/(?P<pk>[\d]+)/$",
        views.RodizioVagasView.as_view(),
        name="view_vagas_resultado_psct",
    ),
]
