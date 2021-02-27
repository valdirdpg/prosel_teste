"""
Arquivo modelo do settings.py.
Aqui deve conter apenas o que há de diferente em relação ao settings_sample.py,
como por exemplo senhas e outros dados sigilosos.
"""

import os
import raven

if os.environ.get("DATABASE_URL", False):
    from portaldocandidato.settings_base_dokku import *
else:
    from portaldocandidato.settings_base import *

ALLOWED_HOSTS = ["*"]
DEBUG = not bool(ALLOWED_HOSTS)

SITE_URL = DEBUG and "http://localhost:8000" or "https://estudante.ifpb.edu.br"

ADMINS = [("Admin", "estudante.debug@ifpb.edu.br")]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASS"],
        "HOST": os.environ["DB_HOST"],
        "PORT": "5432",
    }
}

RECAPTCHA_PRIVATE_KEY = os.environ["RECAPTCHA_PRIVATE_KEY"]
RECAPTCHA_PUBLIC_KEY = os.environ["RECAPTCHA_PUBLIC_KEY"]
SUAP_AUTH_TOKEN = os.environ["SUAP_AUTH_TOKEN"]

EMAIL_HOST = os.environ["EMAIL_HOST"]
EMAIL_PORT = os.environ["EMAIL_HOST_PORT"]
EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"]
EMAIL_SUBJECT_PREFIX = "[IFPB-ESTUDANTE] "
EMAIL_USE_TLS = True

EMAIL_FROM = os.environ["EMAIL_FROM"]
EMAIL_REPLY_TO = EMAIL_FROM

RAVEN_CONFIG = {
    "dsn": os.environ["RAVEN_DSN"],
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    "release": raven.fetch_git_sha(os.path.join(os.path.dirname(__file__), "..")),
}


BROKER_URL = os.environ["BROKER_URL"]
CELERY_RESULT_BACKEND = os.environ["CELERY_RESULT_BACKEND"]


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": os.environ["MEMCACHED_LOCATION"],
    }
}

EMAIL_BACKEND = os.environ["EMAIL_BACKEND"]
JAIMINHO_URL = os.environ["JAIMINHO_URL"]
JAIMINHO_TOKEN = os.environ["JAIMINHO_TOKEN"]
JAIMINHO_APP_ID = os.environ["JAIMINHO_APP_ID"]
