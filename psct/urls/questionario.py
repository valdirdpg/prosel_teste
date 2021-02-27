from django.conf.urls import url

from psct.views import questionario as views

urlpatterns = [
    url(
        "questionario_socioeconomico/(?P<edital_pk>[0-9]+)/$",
        views.QuestionarioCreate.as_view(),
        name="responder_questionario_psct",
    )
]
