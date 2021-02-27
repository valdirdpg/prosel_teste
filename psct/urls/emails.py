from django.conf.urls import url

from psct.views import emails as views

urlpatterns = [
    url(
        "^emails/(?P<pk>[0-9]+)/$",
        views.SolicitacaoEmailView.as_view(),
        name="enviar_email_psct",
    )
]
