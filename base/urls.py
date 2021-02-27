from django.conf.urls import url

from base import views

urlpatterns = [
    url(r"^busca/$", views.SearchView.as_view(), name="busca"),
    url(r"^busca/(?P<q>\w+)/$", views.SearchView.as_view(), name="buscar"),
]
