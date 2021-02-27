from portaldocandidato.settings_base import *

import dj_database_url


DATABASES = {}
DATABASES["default"] = dj_database_url.config()

SUAP_AUTH_TOKEN = os.environ.get("SUAP_AUTH_TOKEN", "")
RECAPTCHA_PRIVATE_KEY = os.environ.get("RECAPTCHA_PRIVATE_KEY", "")
RECAPTCHA_PUBLIC_KEY = os.environ.get("RECAPTCHA_PUBLIC_KEY", "")

ALLOWED_HOSTS = ["*"]
DEBUG = True

SITE_URL = DEBUG and "http://localhost:8000" or "https://estudante.ifpb.edu.br"

ADMINS = ("Admin", "admin@example.net")

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "suaprest.django.auth.SUAPAuthBackend",
]


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": os.environ["MEMCACHED_URL"].replace("memcached://", ""),
    }
}

BROKER_URL = os.environ["RABBITMQ_URL"]
CELERY_RESULT_BACKEND = os.environ["REDIS_URL"]


# Minio storage configuration in settings.py

STATICFILES_STORAGE = "base.storages.MinioAssestsStorage"
DEFAULT_FILE_STORAGE = "base.storages.MinioPublicMediaStorage"

MINIO_URL = os.environ["MINIO_URL"]
MINIO_ACCESS_KEY = os.environ["MINIO_ACCESS_KEY"]
MINIO_SECRET_KEY = os.environ["MINIO_SECRET_KEY"]
MINIO_MEDIA_BUCKET_NAME = os.environ["MEDIA_BUCKET_NAME"]
MINIO_AUTO_CREATE_BUCKET = True
MINIO_PUBLIC_BUCKET_NAME = os.environ["STATIC_BUCKET_NAME"]
MINIO_ASSETS_LOCATION = "static"
MINIO_MEDIA_LOCATION = "media"
AWS_DEFAULT_ACL = None
MINIO_PUBLIC_ACL = "public-read"
MINIO_PUBLIC_QUERYSTRING_AUTH = False
MINIO_PRIVATE_ACL = "private"
MINIO_DEFAULT_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}
