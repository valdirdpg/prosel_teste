from django.contrib import admin
from django.utils.safestring import mark_safe

from psct.models.emails import Email


class EmailAdmin(admin.ModelAdmin):
    list_display = ("assunto", "enviar")

    @mark_safe
    def enviar(self, obj):
        return '<a href="/psct/emails/{}" class="btn btn-default btn-xs">Enviar</a>'.format(
            obj.id
        )

    enviar.short_description = "Ações"


admin.site.register(Email, EmailAdmin)
