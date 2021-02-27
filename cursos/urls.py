from django.urls import path

from cursos import views

urlpatterns = [
    path("", views.CursoListView.as_view(), name="cursos"),
    path("<int:pk>/", views.CursoView.as_view(), name="curso"),
    path(
        "<int:pk>/editar/",
        views.CursoNoCampusUpdateView.as_view(),
        name="cursonocampus_update",
    ),
    path("contato/", views.ContactListView.as_view(), name="contato"),
    path("polo/<int:pk>/", views.ContactView.as_view(), {"tipo": "polo"}, name="polo"),
    path(
        "campus/<int:pk>/",
        views.ContactView.as_view(),
        {"tipo": "campus"},
        name="campus",
    ),
    path(
        "importar_docentes/",
        views.ImportarDocentesView.as_view(),
        name="importar_docentes",
    ),
    path(
        "autocomplete-servidor/",
        views.AutoCompleteServidor.as_view(),
        name="autocomplete_servidor",
    ),
    path(
        "autocomplete-docente/",
        views.AutoCompleteServidor.as_view(docente=True),
        name="autocomplete_docente",
    ),
    path(
        "autocomplete-disciplina/",
        views.AutoCompleteDisciplina.as_view(),
        name="autocomplete_disciplina",
    ),
    path(
        "autocomplete-user/", views.AutoCompleteUser.as_view(), name="autocomplete_user"
    ),
    path("servidor/", views.ServidorListView.as_view(), name="servidor_changelist"),
    path("servidor/add/", views.ServidorCreateView.as_view(), name="servidor_add"),
    path(
        "servidor/<int:pk>/change/",
        views.ServidorUpdateView.as_view(),
        name="servidor_change",
    ),
    path(
        "campus/<int:pk_campus>/permissoes/",
        views.PermissoesUsuariosCampusListView.as_view(),
        name="permissoes_campus",
    ),
    path(
        "campus/<int:pk_campus>/servidor/add/",
        views.AdicionarUsuarioCampusView.as_view(),
        name="adicionar_usuario_campus",
    ),
    path(
        "campus/<int:pk_campus>/servidor/<int:pk_user>/delete/",
        views.RemoverUsuarioCampusView.as_view(),
        name="remover_usuario_campus",
    ),
    path(
        "campus/<int:pk_campus>/servidor/<int:pk_user>/permissoes/",
        views.GerenciarPermissaoUsuarioCampusView.as_view(),
        name="gerenciar_permissoes_usuario_campus",
    ),
]
