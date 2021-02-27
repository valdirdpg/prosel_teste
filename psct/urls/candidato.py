from django.conf.urls import url

from psct.views import candidato as views

urlpatterns = [
    url(r"^$", views.PSCTView.as_view(), name="index_psct"),
    url(
        "^cadastro_candidato/$",
        views.PreCadastroCandidatoFormView.as_view(),
        name="pre_cadastro_candidato_psct",
    ),
    url("^dados_basicos/$", views.CandidatoView.as_view(), name="dados_basicos_psct"),
    url(
        r"^dados_basicos/(?P<pk>[\d]+)$",
        views.CandidatoUpdateView.as_view(),
        name="dados_basicos_update_psct",
    ),
    url(
        "^candidato_dados_basicos/$",
        views.CandidatoDadosBasicosRedirectView.as_view(),
        name="dados_basicos_redirect",
    ),
    url(
        "^importar_sisu/$",
        views.CandidatoImportarSISU.as_view(),
        name="importar_candidato_sisu_psct",
    ),
]
