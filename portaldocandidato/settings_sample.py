"""
Arquivo modelo do settings.py.
Aqui deve conter apenas o que há de diferente em relação ao settings_sample.py,
como por exemplo senhas e outros dados sigilosos.
"""

import os
import sys

from portaldocandidato.settings_base import *

ALLOWED_HOSTS = []
DEBUG = not bool(ALLOWED_HOSTS)

SITE_URL = DEBUG and "http://localhost:8000" or "https://estudante.ifpb.edu.br"

ADMINS = ("Admin", "admin@example.net")

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "",
        "USER": "",
        "PASSWORD": "",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "127.0.0.1:11211",
    }
}

if DEBUG and 'test' in sys.argv:
    IFPB_PERMISSIONS_GROUP_CACHE = False

BROKER_URL = "amqp://"
CELERY_RESULT_BACKEND = "redis://"
