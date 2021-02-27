from django.conf import settings
from django.core.exceptions import ValidationError

MB = 1024 * 1024


def validate_file_size(value):
    max_size = 2 * MB
    try:
        filesize = value.size
        if filesize > max_size:
            raise ValidationError("Arquivo não pode ser maior que 2MB!")
    except FileNotFoundError as error:
        if not settings.DEBUG:
            raise error


def validate_file_type(value):
    valid_types = ["pdf"]
    try:
        if hasattr(value.file, "content_type"):
            filetype = value.file.content_type.split("/")[1]
            if filetype not in valid_types:
                raise ValidationError("Arquivo não suportado!")
    except FileNotFoundError as error:
        if not settings.DEBUG:
            raise error
