import mimetypes
from os.path import splitext

from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.deconstruct import deconstructible

DOCUMENT_EXTENSIONS = ["pdf"]


@deconstructible
class FileValidator:
    """
    Validator for files, checking the size, extension and mimetype.

    Initialization parameters:
        allowed_extensions: iterable with allowed file extensions
            ie. ('txt', 'doc')
        allowd_mimetypes: iterable with allowed mimetypes
            ie. ('image/png', )
        min_size: minimum number of bytes allowed
            ie. 100
        max_size: maximum number of bytes allowed
            ie. 24*1024*1024 for 24 MB

    Usage example::

        MyModel(models.Model):
            myfile = FileField(validators=FileValidator(max_size=24*1024*1024), ...)

    EXAMPLES_TYPES = \
        {'bmp': 'image/x-ms-bmp',
         'doc': 'application/msword',
         'dot': 'application/msword',
         'gif': 'image/gif',
         'ico': 'image/vnd.microsoft.icon',
         'jpe': 'image/jpeg',
         'jpeg': 'image/jpeg',
         'jpg': 'image/jpeg',
         'pdf': 'application/pdf',
         'png': 'image/png',
         'txt': 'text/plain'}

    """

    extension_message = "Extensão '%(extension)s' não permitida. São permitidas as extensões: '%(allowed_extensions)s.'"
    mime_message = "Tipo de arquivo '%(mimetype)s' não é válido. Os tipos permitidos são: %(allowed_mimetypes)s."
    min_size_message = "Arquivo com %(size)s é muito pequeno. O tamanho mínimo permitido é %(allowed_size)s."
    max_size_message = "Arquivo com %(size)s é muito grande. O tamanho máximo permitido é %(allowed_size)s."

    def __init__(self, *args, **kwargs):
        self.allowed_extensions = kwargs.pop("allowed_extensions", [])
        self.allowed_mimetypes = kwargs.pop("allowed_mimetypes", [])
        self.min_size = kwargs.pop("min_size", 0)
        self.max_size = kwargs.pop("max_size", 10 * 1024 * 1024)

    def __call__(self, value):
        """
        Check the extension, content type and file size.
        """
        # Check the extension
        ext = splitext(value.name)[1][1:].lower()
        if self.allowed_extensions and not ext in self.allowed_extensions:
            message = self.extension_message % {
                "extension": ext,
                "allowed_extensions": ", ".join(self.allowed_extensions),
            }

            raise ValidationError(message)

        # Check the content type
        mimetype = mimetypes.guess_type(value.name)[0]
        if self.allowed_mimetypes and not mimetype in self.allowed_mimetypes:
            message = self.mime_message % {
                "mimetype": mimetype,
                "allowed_mimetypes": ", ".join(self.allowed_mimetypes),
            }

            raise ValidationError(message)

        # Check the file size
        if not settings.DEBUG:
            filesize = len(value)
        else:
            filesize = 1

        if self.max_size and filesize > self.max_size:
            message = self.max_size_message % {
                "size": filesizeformat(filesize),
                "allowed_size": filesizeformat(self.max_size),
            }

            raise ValidationError(message)

        elif filesize < self.min_size:
            message = self.min_size_message % {
                "size": filesizeformat(filesize),
                "allowed_size": filesizeformat(self.min_size),
            }

            raise ValidationError(message)

    def __eq__(self, other):
        return vars(self) == vars(other)
