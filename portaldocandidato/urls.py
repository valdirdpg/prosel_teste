"""portaldocandidato URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from ajax_select import urls as ajax_select_urls
from processoseletivo import views
handler403 = "base.views.permission_denied"
handler404 = "base.views.page_not_found"
handler500 = "base.views.server_error"
urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^editais/", include("editais.urls")),
    url(r"^processoseletivo/", include("processoseletivo.urls")),
    url(r"^candidatos/", include("candidatos.urls")),
    url(r"^cursos/", include("cursos.urls")),
    url(r"^noticias/", include("noticias.urls")),
    url(r"^base/", include("base.urls")),
    url(r"^acessibilidade/", views.AcessibilidadeView.as_view(), name="acessibilidade"),
    url(r"^$", views.ProcessosView.as_view(), name="processoseletivo"),
    #url(r"^$", views.BaseView.as_view(), name="base"),
    url(r"^candidatos/", include("candidatos.urls")),
    url(r"^psct/", include("psct.urls")),
    url(r"^", include("registration.urls")),
    url(r"^api/", include("api.urls")),
    url(r"^ajax_select/", include(ajax_select_urls)),
    url(r"^ckeditor/", include("ckeditor_uploader.urls")),
    url(r"^suaprest/", include("suaprest.urls")),
    url(r"^monitoring/", include("monitoring.urls")),
]
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    ) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)