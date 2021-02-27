from django.apps import AppConfig


class BaseConfig(AppConfig):
    name = "base"
    verbose_name = "Base"

    def ready(self):
        from model_mommy import mommy, random_gen
        mommy.generators.add(
            "ckeditor_uploader.fields.RichTextUploadingField", random_gen.gen_file_field
        )

