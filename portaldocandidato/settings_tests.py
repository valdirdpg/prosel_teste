"""
Arquivo modelo do settings.py.
Aqui deve conter apenas o que há de diferente em relação ao settings_sample.py,
como por exemplo senhas e outros dados sigilosos.
"""

import os

if os.environ.get("DATABASE_URL", False):
    from portaldocandidato.settings_dokku import *
else:
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
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "postgres",
        "PORT": "5432",
    }
}


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "memcached:11211",
    }
}

IFPB_PERMISSIONS_GROUP_CACHE = False

BROKER_URL = "amqp://rabbitmq"
CELERY_RESULT_BACKEND = "redis://redis"
