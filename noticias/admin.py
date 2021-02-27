from django.contrib import admin
from image_cropping import ImageCroppingMixin

from noticias.forms import AssuntoForm, NoticiaForm, PalavrasChaveForm
from noticias.models import Assunto, Noticia, PalavrasChave


class NoticiaAdmin(ImageCroppingMixin, admin.ModelAdmin):
    list_display = (
        "titulo",
        "criacao",
        "assunto",
        "publicado_display",
        "destaque_display",
    )
    list_filter = ("assunto", "publicado", "destaque")
    date_hierarchy = "criacao"
    form = NoticiaForm

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.user = request.user
        return form


class PalavrasChaveAdmin(admin.ModelAdmin):
    form = PalavrasChaveForm


class AssuntoAdmin(admin.ModelAdmin):
    list_display = ("nome", "pagina_inicial", "noticias_count")
    form = AssuntoForm

    fieldsets = (
        (None, {"fields": ("nome",)}),
        (
            "Personalize a exibição na página inicial",
            {
                "classes": ("collapse",),
                "fields": ("pagina_inicial", "cor", "quantidade"),
            },
        ),
    )

    def noticias_count(self, obj):
        return obj.noticia_set.count()

    noticias_count.short_description = "Total de Notícias"


admin.site.register(Noticia, NoticiaAdmin)
admin.site.register(PalavrasChave, PalavrasChaveAdmin)
admin.site.register(Assunto, AssuntoAdmin)
