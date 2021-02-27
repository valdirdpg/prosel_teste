from django.apps import apps
from django.utils.module_loading import import_string
from rest_framework import routers


def get_router():
    router = routers.DefaultRouter()
    for app_config in apps.get_app_configs():
        try:
            module_name = app_config.module.__name__ + ".api.router.router"
            router_data = import_string(module_name)
            for name, viewset in router_data:
                router.register(name, viewset)
        except ImportError:
            pass

    return router
