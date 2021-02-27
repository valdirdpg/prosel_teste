from django.conf.urls import include, url

urlpatterns = [
    url(r"", include("psct.urls.questionario")),
    url(r"", include("psct.urls.inscricao")),
    url(r"", include("psct.urls.candidato")),
    url(r"", include("psct.urls.recurso")),
    url(r"", include("psct.urls.consulta")),
    url(r"", include("psct.urls.emails")),
    url(r"", include("psct.urls.analise")),
    url(r"", include("psct.urls.relatorios")),
    url(r"", include("psct.urls.pontuacao")),
    url(r"", include("psct.urls.resultado")),
    url(r"", include("psct.urls.audit")),
    url(r"", include("psct.urls.indeferimento")),
    url(r"prematricula", include("psct.urls.prematricula")),
]
