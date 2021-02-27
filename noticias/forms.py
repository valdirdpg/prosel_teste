from datetime import datetime

from django import forms
from django.utils.text import slugify

from noticias import models


class NoticiaForm(forms.ModelForm):
    def save(self, *args, **kwargs):
        self.instance.responsavel = self.user
        self.instance.atualizacao = datetime.now()
        self.instance.slug = slugify(self.instance.titulo)
        return super().save(*args, **kwargs)

    class Meta:
        model = models.Noticia
        exclude = ("criacao", "atualizacao", "responsavel", "slug")


class PalavrasChaveForm(forms.ModelForm):
    def save(self, *args, **kwargs):
        self.instance.slug = slugify(self.instance.palavra)
        return super().save(*args, **kwargs)

    class Meta:
        model = models.Noticia
        exclude = ("slug",)


class AssuntoForm(forms.ModelForm):
    def save(self, *args, **kwargs):
        self.instance.slug = slugify(self.instance.nome)
        return super().save(*args, **kwargs)

    class Meta:
        model = models.Assunto
        exclude = ("slug",)
        labels = {"pagina_inicial": "Exibir na página inicial?"}
