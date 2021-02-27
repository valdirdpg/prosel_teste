from django.db.models.fields.files import FileField

from base.validators import FileValidator


class DocumentFileField(FileField):
    """
    Permite definir um campo do modelo como FileField com validação de tamanho e formato. Por padrão, o campo irá validar
    arquivos com extensão .pdf e tamanho de 2MB. Esses valores são personalizáveis

    Exemplo de uso:
        class MeuModelo(models.Model)
            file = DocumentFileField(verbose_name=u'Arquivo', upload_to='documentos', size=3, format=['pdf', 'doc'])
    """

    HELP_TEXT = "Somente arquivo {} com até {} MB."

    def __init__(self, *args, **kwargs):
        default_size = kwargs.pop("size", 2)
        default_format = kwargs.pop("format", ["pdf"])
        format_as_text = ", ".join(default_format[0:-1]) + " ou " + default_format[-1]
        kwargs.setdefault("max_length", 255)
        kwargs.setdefault(
            "help_text", self.HELP_TEXT.format(format_as_text, str(default_size))
        )
        kwargs.setdefault(
            "validators",
            [
                FileValidator(
                    max_size=default_size * 1024 * 1024,
                    allowed_extensions=default_format,
                )
            ],
        )
        self.widget_attrs = kwargs.pop("widget_attrs", {})
        if "width" in kwargs:
            self.widget_attrs["style"] = f"width: {kwargs.pop('width')}px;"
        super().__init__(*args, **kwargs)
