from django.conf.urls import url

from psct.views import consulta as views

urlpatterns = [
    url(
        "^consulta/(?P<pk>[0-9]+)/$",
        views.ViewConsulta.as_view(),
        name="visualizar_consulta_psct",
    ),
    url("^dashboard-psct/$", views.DashboardView.as_view(), name="dashboard-psct"),
]
