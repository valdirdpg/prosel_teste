from django.conf.urls import include, url
from rest_framework.authtoken import views
from rest_framework.schemas import get_schema_view
from rest_framework_swagger.views import get_swagger_view

from api.default_router import get_router

schema_view = get_schema_view(title="Portal do Candidato API")
swagger_view = get_swagger_view(title="Portal do Candidato API")


router = get_router()
urlpatterns = [
    url(r"", include(router.urls)),
    url(r"^auth/", include("rest_framework.urls", namespace="rest_framework")),
    url(r"^schema/$", schema_view),
    url(r"^swagger/$", swagger_view),
    url(r"^token/$", views.obtain_auth_token),
]
