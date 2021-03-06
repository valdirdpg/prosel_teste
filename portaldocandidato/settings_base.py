"""
Django settings for portaldocandidato project.

Generated by 'django-admin startproject' using Django 1.8.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the' full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""



# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "0y-u-ips%yo-^bhq$28w8nswr$_%vet-ywlze5%%+$sp3jg)q&"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

# Application definition

CKEDITOR_CONFIGS = {
    "default": {"toolbar": "Full"},
    "noticias": {
        "toolbar": "Custom",
        "toolbar_Custom": [
            ["Bold", "Italic", "Underline"],
            [
                "NumberedList",
                "BulletedList",
                "-",
                "Outdent",
                "Indent",
                "-",
                "JustifyLeft",
                "JustifyCenter",
                "JustifyRight",
                "JustifyBlock",
            ],
            ["Link", "Unlink"],
            ["RemoveFormat", "Source"],
        ],
    },
    "editais": {
        "toolbar": "Custom",
        "toolbar_Custom": [
            ["NewPage", "Preview", "-", "Templates"],
            ["Undo", "Redo"],
            ["Styles", "Format", "Font", "FontSize"],
            ["Bold", "Italic", "Underline", "Strike", "-", "Subscript", "Superscript"],
            ["TextColor", "BGColor"],
            [
                "NumberedList",
                "BulletedList",
                "-",
                "Outdent",
                "Indent",
                "Blockquote",
                "-",
                "RemoveFormat",
            ],
            ["JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"],
            ["Link", "Unlink", "Anchor"],
            ["Image", "Table", "HorizontalRule", "Smiley", "SpecialChar", "PageBreak"],
            ["Maximize", "ShowBlocks", "Source"],
        ],
    },
    "processoseletivo": {
        "toolbar": "Custom",
        "toolbar_Custom": [
            ["NewPage", "Preview", "-", "Templates"],
            ["Undo", "Redo"],
            ["Styles", "Format", "Font", "FontSize"],
            ["Bold", "Italic", "Underline", "Strike", "-", "Subscript", "Superscript"],
            ["TextColor", "BGColor"],
            [
                "NumberedList",
                "BulletedList",
                "-",
                "Outdent",
                "Indent",
                "Blockquote",
                "-",
                "RemoveFormat",
            ],
            ["JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"],
            ["Link", "Unlink", "Anchor"],
            ["Image", "Table", "HorizontalRule", "Smiley", "SpecialChar", "PageBreak"],
            ["Maximize", "ShowBlocks", "Source"],
        ],
    },
}

# Aplicações padrão do Django

APPS_DJANGO_DEFAULTS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.postgres",
)

# Plugins que adicionamos

APPS_PLUGINS = (
    "dal",
    "dal_select2",
    "django_extensions",
    "ckeditor",
    "ckeditor_uploader",
    "bootstrap3",
    "bootstrap_pagination",
    "snowpenguin.django.recaptcha2",
    "betterforms",
    "form_utils",
    "easy_thumbnails",
    "image_cropping",
    "raven.contrib.django.raven_compat",
    "reversion",
    "reversion_compare",
    "ajax_select",
    "django_google_charts",
    "suaprest",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_swagger",
    "django_filters",
    "behave_django",
)

# Aplicações desenvolvidas

APPS_OURS = (
    "base",
    "candidatos.apps.CandidatosConfig",
    "cursos.apps.CursosConfig",
    "editais.apps.EditaisConfig",
    "processoseletivo.apps.ProcessoSeletivoConfig",
    "noticias.apps.NoticiasConfig",
    "registration",
    "psct.apps.PSCTConfig",
    "api.apps.ApiConfig",
    "monitoring.apps.MonitoringConfig",
)

INSTALLED_APPS = APPS_DJANGO_DEFAULTS + APPS_PLUGINS + APPS_OURS


from easy_thumbnails.conf import Settings as thumbnail_settings

THUMBNAIL_PROCESSORS = (
    "image_cropping.thumbnail_processors.crop_corners",
) + thumbnail_settings.THUMBNAIL_PROCESSORS

IMAGE_CROPPING_BACKEND = "image_cropping.backends.easy_thumbs.EasyThumbnailsBackend"
IMAGE_CROPPING_BACKEND_PARAMS = {}


MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "base.middleware.usersession.UserSessionMiddleware",
)

ROOT_URLCONF = "portaldocandidato.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "base.context_processors.config",
                "base.context_processors.apps_list",
                "base.context_processors.debug",
                "ifpb_django_menu.context_processors.get_user_menu",
            ]
        },
    }
]

WSGI_APPLICATION = "portaldocandidato.wsgi.application"

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = "pt-br"

LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]

TIME_ZONE = "America/Recife"

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_ROOT = os.path.join(STATIC_ROOT, "media")
MEDIA_URL = "/media/"

STATICFILES_DIRS = (os.path.join(BASE_DIR, "templates", "publico"),)

CKEDITOR_UPLOAD_PATH = "uploads/"

RECAPTCHA_PRIVATE_KEY = "6LefXUcaAAAAAPWEqMfu5XFUDE9mCj9Yc_2socEH"
RECAPTCHA_PUBLIC_KEY = "6LefXUcaAAAAANdDoEC11dcDtu1vDDzRe5o9OMeZ"

SUAP_AUTH_TOKEN = "4f21943b1fddc8e1db4b9f24aee564aa628161bc"
SUAP_DOMAIN = "http://10.1.0.86:8080"
SUAP_AUTH_INFO_URL = "http://10.1.0.86:8080/ldap_backend/info/"
SUAP_AUTH_LOGIN_URL = "http://10.1.0.86:8080/ldap_backend/auth/"
SUAP_URL = "http://10.1.10.86:8080"
# SUAP_AUTH_TOKEN = "4f21943b1fddc8e1db4b9f24aee564aa628161bc"
# SUAP_DOMAIN = "https://suap.ifba.edu.br"
# SUAP_AUTH_INFO_URL = "https://suap.ifba.edu.br/ldap_backend/info/"
# SUAP_AUTH_LOGIN_URL = "https://suap.ifba.edu.br/ldap_backend/auth/"
# SUAP_URL = "https://suap.ifba.edu.br/"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "suaprest.django.auth.SUAPAuthBackend",
]

LOGIN_URL = "/login/"

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE_PSCT = 30 * 60  # 30 minutos

EMAIL_FROM = "selecao@ifba.edu.br"
EMAIL_REPLY_TO = EMAIL_FROM

BROKER_URL = ""
CELERY_RESULT_BACKEND = ""

CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

CELERY_SEND_TASK_ERROR_EMAILS = True

CELERY_IMPORTS = ["psct.tasks"]


SUAP_REST_ADMIN_USER = True


REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DATE_FORMAT": "%d/%m/%Y",
    "DATETIME_FORMAT": "%d/%m/%Y %H:%M",
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
}

SWAGGER_SETTINGS = {"LOGOUT_URL": "/logout/", "LOGIN_URL": "/psct/login/"}

FILE_UPLOAD_PERMISSIONS = 0o644

DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000