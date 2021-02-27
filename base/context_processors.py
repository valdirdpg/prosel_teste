from django.conf import settings
from django.contrib import admin

from base.configs import PortalConfig
from noticias import models


def config(request):
    return {"config": PortalConfig, "assuntos": models.Assunto.objects.all()}


def apps_list(request):
    return {"estudante_app_list": admin.site.get_app_list(request)}


def debug(request):
    return {"DEBUG": settings.DEBUG}
