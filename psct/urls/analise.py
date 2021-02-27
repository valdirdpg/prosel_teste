from django.conf.urls import url

from psct.views import analise as views

urlpatterns = [
    url(
        "^analise/inscricao/$",
        views.ListInscricaoView.as_view(),
        name="list_inscricao_psct",
    ),
    url(
        r"^analise/lote/avaliador/(?P<fase_pk>[\d]+)/(?P<quantidade>[\d]+)/$",
        views.CreateLoteAvaliadorInscricaoView.as_view(),
        name="add_lote_avaliador_inscricao_psct",
    ),
    url(
        r"^analise/lote/homologador/(?P<fase_pk>[\d]+)/(?P<quantidade>[\d]+)/$",
        views.CreateLoteHomologadorInscricaoView.as_view(),
        name="add_lote_homologador_inscricao_psct",
    ),
    url(
        r"^analise/importar_inscricao/(?P<fase_pk>[\d]+)/$",
        views.ImportarInscricaoView.as_view(),
        name="analise_importar_inscricao_psct",
    ),
    url(
        "^analise/redistribuir/avaliador/(?P<fase_pk>[0-9]+)/$",
        views.RedistribuirInscricaoAvaliacaoView.as_view(),
        name="redistribuir_inscricao_avaliador_psct",
    ),
    url(
        "^analise/redistribuir/homologador/(?P<fase_pk>[0-9]+)/$",
        views.RedistribuirInscricaoHomologadorView.as_view(),
        name="redistribuir_inscricao_homologador_psct",
    ),
    url(
        "^analise/(?P<fase_pk>[0-9]+)/regras/$",
        views.RegraExclusaoView.as_view(),
        name="regra_exclusao_inscricao_psct",
    ),
    url(
        "^analise/(?P<fase_pk>[0-9]+)/(?P<coluna_pk>[0-9]+)/grupo/$",
        views.GrupoRegraExclusaoView.as_view(),
        name="grupo_regra_exclusao_inscricao_psct",
    ),
    url(
        r"^analise/avaliacao/(?P<inscricao_pk>[\d]+)/avaliador/add/$",
        views.CreateAvaliacaoAvaliadorInscricaoView.as_view(),
        name="add_avaliacao_avaliador_inscricao_psct",
    ),
    url(
        r"^analise/avaliacao/(?P<pk>[\d]+)/avaliador/change/$",
        views.UpdateAvaliacaoAvaliadorInscricaoView.as_view(),
        name="change_avaliacao_avaliador_inscricao_psct",
    ),
    url(
        r"^analise/avaliacao/avaliador/(?P<pk>[\d]+)/$",
        views.AvaliacaoAvaliadorView.as_view(),
        name="view_avaliacao_avaliador_inscricao_psct",
    ),
    url(
        r"^analise/avaliacao/(?P<inscricao_pk>[\d]+)/homologador/add/$",
        views.CreateAvaliacaoHomologadorInscricaoView.as_view(),
        name="add_avaliacao_homologador_inscricao_psct",
    ),
    url(
        r"^analise/avaliacao/(?P<pk>[\d]+)/homologador/change/$",
        views.UpdateAvaliacaoHomologadorInscricaoView.as_view(),
        name="change_avaliacao_homologador_inscricao_psct",
    ),
    url(
        r"^analise/avaliacao/homologador/(?P<pk>[\d]+)/$",
        views.AvaliacaoHomologadorView.as_view(),
        name="view_avaliacao_homologador_inscricao_psct",
    ),
    url(
        r"^analise/avaliacao/adminview/(?P<pk>[\d]+)/$",
        views.AvaliacaoAdminView.as_view(),
        name="view_avaliacao_inscricao_psct",
    ),
]
