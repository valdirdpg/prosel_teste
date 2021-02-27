from django.conf.urls import url

from editais import views

urlpatterns = [
    url(
        r"^(?P<pk>[\d]+)/view$", views.EditalDetailView.as_view(), name="edital-detail"
    ),
    url(
        r"^(?P<pk_edital>[\d]+)/(?P<categoria>[\w]+)/view$",
        views.EditalArquivosView.as_view(),
        name="arquivos_edital",
    ),
    url(r"^$", views.EditalView.as_view(), name="editais"),
    url(
        r"^encerrados$",
        views.EditaisEncerradosView.as_view(),
        name="editais_encerrados",
    ),
]
