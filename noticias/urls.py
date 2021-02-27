from django.conf.urls import url

from noticias import views

urlpatterns = [
    url(r"^$", views.NoticiasListView.as_view(), name="noticias"),
    url(
        r"^assunto/(?P<slug>[\w-]+)/$",
        views.NoticiasAssuntoListView.as_view(),
        name="assunto",
    ),
    url(
        r"^tag/(?P<slug>[\w-]+)/$",
        views.NoticiasPChaveListView.as_view(),
        name="palavra_chave",
    ),
    url(
        r"^(?P<slug>[\w-]+)/$", views.NoticiaDetailView.as_view(), name="noticia-detail"
    ),
]
