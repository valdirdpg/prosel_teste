import importlib
import os
import sys

from django.apps import apps
from django.conf import settings


def find_files_from_apps(filename):
    result = []
    for app in apps.get_app_configs():
        filepath = os.path.join(app.path, filename)
        if os.path.exists(filepath):
            result.append(filepath)
    return result


def import_module_from_apps(module_name):
    result = []

    for app in apps.get_app_configs():
        filepath = os.path.join(app.path, module_name + ".py")
        if os.path.exists(filepath):
            module_name = f"{app.name}.{module_name}"

            module = importlib.import_module(module_name)

            if settings.DEBUG:
                if module_name in sys.modules:
                    importlib.reload(module)

            result.append(module)

    return result
