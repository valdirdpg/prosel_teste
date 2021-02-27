from django.urls import path

from candidatos import views

urlpatterns = [
    path(
        "dados_basicos_candidato/",
        views.DadosBasicosUpdateView.as_view(),
        name="dados_basicos_candidato",
    ),
    path(
        "dados_basicos_prematricula/",
        views.CandidatoUpdateView.as_view(),
        name="dados_basicos_prematricula",
    ),
    path(
        "<int:pk_candidato>/caracterizacao/adicionar/",
        views.CaracterizacaoCreateView.as_view(),
        name="adicionar_caracterizacao_prematricula",
    ),
    path(
        "<int:pk_candidato>/caracterizacao/editar/",
        views.CaracterizacaoUpdateView.as_view(),
        name="editar_caracterizacao_prematricula",
    ),
    path(
        "chamadas/", views.ChamadasCandidatoView.as_view(), name="chamadas_prematricula"
    ),
    path(
        "convocacoes/",
        views.ConvocacoesCandidatoView.as_view(),
        name="candidato_convocacoes",
    ),
    path(
        "<int:candidato_pk>/chamada/<int:chamada_pk>/imprimir/",
        views.imprimir_prematricula,
        name="imprimir_prematricula",
    ),
    path(
        "<int:pk>/recursos/",
        views.RecursosCandidatoView.as_view(),
        name="recursos_candidato",
    ),
]
