from django.conf.urls import url

from psct.views import indeferimento as views

urlpatterns = [
    url(
        r"^add_indeferimento_especial/(?P<inscricao_pk>[\d]+)/$",
        views.CreateIndeferimentoEspecialView.as_view(),
        name="add_indeferimento_especial",
    ),
    url(
        r"^change_indeferimento_especial/(?P<pk>[\d]+)/$",
        views.UpdateIndeferimentoEspecialView.as_view(),
        name="change_indeferimento_especial",
    ),
    url(
        r"^delete_indeferimento_especial/(?P<pk>[\d]+)/$",
        views.DeleteIndeferimentoEspecialView.as_view(),
        name="delete_indeferimento_especial",
    ),
]
