from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import text
from django.utils.safestring import mark_safe
from image_cropping import ImageRatioField

from base import choices


class NoticiaQuerySet(models.QuerySet):
    def publicadas(self):
        return self.filter(publicado=True)

    def destaques(self, assunto=None):
        destaques = self.publicadas().filter(destaque=True)
        if assunto:
            return destaques.filter(assunto=assunto)
        return destaques


class AssuntoQuerySet(models.QuerySet):
    def pagina_inicial(self):
        return self.filter(pagina_inicial=True)


class PalavrasChave(models.Model):
    palavra = models.CharField(max_length=30, unique=True)
    slug = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.palavra

    class Meta:
        ordering = ("palavra",)


class Assunto(models.Model):
    nome = models.CharField(max_length=30, unique=True)
    pagina_inicial = models.BooleanField(
        verbose_name="Página Inicial",
        default=False,
        help_text="Marque se desejar que as notícias mais recentes deste grupo sejam exibidas na página inicial.",
    )
    cor = models.CharField(
        max_length=255,
        choices=choices.Cor.choices(),
        default=choices.Cor.VERDE_ESCURO.value,
        help_text="Escolha a cor do título a ser exibido para este grupo de notícias.",
    )
    quantidade = models.IntegerField(
        verbose_name="Quantidade de notícias exibidas",
        help_text="Informe um número maior que zero e múltiplo de 3. Ex.: 3, 6, 9, etc.",
        default=3,
    )
    slug = models.SlugField(unique=True)

    objects = AssuntoQuerySet.as_manager()

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse("assunto", kwargs={"slug": text.slugify(self.nome)})

    def cor_to_css(self):
        return choices.Cor.label(self.cor)

    @property
    def noticia_mais_recente(self):
        return self.noticia_set.first()

    def clean(self):
        if self.quantidade == 0 or self.quantidade % 3 != 0:
            raise ValidationError(
                {
                    "quantidade": "A quantidade de notícias deve ser um número maior que zero e múltiplo de 3."
                }
            )


def generate_imagem_noticia_path(self, filename):
    url = f"noticias/imagens/{filename}"
    return url


class Noticia(models.Model):
    titulo = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    corpo = RichTextField(config_name="noticias")
    resumo = models.CharField(
        max_length=200, help_text="Descrição da notícia a ser publicada."
    )
    criacao = models.DateTimeField(db_index=True, auto_now_add=True)
    atualizacao = models.DateTimeField(db_index=True, auto_now=True)
    responsavel = models.ForeignKey(User, on_delete=models.CASCADE)
    imagem = models.ImageField(
        upload_to=generate_imagem_noticia_path,
        help_text="Ao concluir o preenchimento do formulário, clique em 'Salvar e continuar "
        "editando' para personalizar o tamanho da imagem. ",
    )
    cropping = ImageRatioField(
        "imagem",
        "460x272",
        verbose_name="Imagem que será exibida",
        help_text="Clique e arraste para formar a área da imagem que será exibida no portal",
    )
    texto_alternativo = models.CharField(
        max_length=100,
        help_text="Descreva a imagem. Será utilizado quando a imagem não puder ser "
        "carregada e quando o usuário estiver utilizando um leitor de tela.",
    )
    palavras_chave = models.ManyToManyField(PalavrasChave)
    publicado = models.BooleanField(default=False)
    destaque = models.BooleanField(default=False)
    assunto = models.ForeignKey(Assunto, on_delete=models.CASCADE)

    objects = NoticiaQuerySet.as_manager()

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("noticia-detail", kwargs={"slug": self.slug})

    def get_absolute_url_img(self):
        return self.imagem.url

    def publicado_display(self):
        return mark_safe(
            '<span class="badge">{}</span>'.format(
                "Publicado" if self.publicado else "Rascunho"
            )
        )

    publicado_display.short_description = "Publicado"
    publicado_display.admin_order_field = "publicado"

    def destaque_display(self):
        return mark_safe(
            f"<span class=\"badge\">{('Sim' if self.destaque else 'Não')}</span>"
        )

    destaque_display.short_description = "Destaque"
    destaque_display.admin_order_field = "destaque"

    class Meta:
        verbose_name = "Notícia"
        verbose_name_plural = "Notícias"
        ordering = ["-criacao"]
