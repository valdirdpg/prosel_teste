from django.conf.urls import url

from psct.views import audit as views

urlpatterns = [
    url(
        "^audit/inscricao/(?P<pk>[0-9]+)/history/$",
        views.InscricaoHistoryView.as_view(),
        name="inscricao_history_psct",
    ),
    url(
        "^audit/candidato/(?P<pk>[0-9]+)/history/$",
        views.CandidatoHistoryView.as_view(),
        name="candidato_history_psct",
    ),
    url(
        "^audit/revision/(?P<pk>[0-9]+)/view/$",
        views.RevisionDetailView.as_view(),
        name="revision_view_psct",
    ),
]
