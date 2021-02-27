from django.conf.urls import url

from psct.views import prematricula as views

urlpatterns = [
    url(
        r"^inscricao/(?P<pk>[\d]+)/",
        views.DadosInscricaoView.as_view(),
        name="prematricula_inscricao_psct",
    ),
    url(
        "^inscricao/", views.ListInscricaoView.as_view(), name="list_prematricula_psct"
    ),
    url("^ccas/", views.ListCCAView.as_view(), name="list_ccas_psct"),
]
