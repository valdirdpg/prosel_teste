from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from psct import models
from psct.admin.reversion import PermissionCompareVersionAdmin


class CandidatoAdmin(PermissionCompareVersionAdmin):
    fields = ("cpf", "nome", "email")
    readonly_fields = ("cpf", "nome")
    list_display = ("nome", "cpf", "telefone", "auditoria")
    search_fields = ("cpf", "nome", "email", "user__username")
    change_list_template = "admin/psct/candidato/change_list.html"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if obj:
            return request.user.is_staff and request.user.has_perms(
                ["psct.admin_can_change_email", "psct.change_candidato"]
            )
        return request.user.has_perm("psct.list_candidato") or request.user.has_perm(
            "psct.change_candidato"
        )

    @mark_safe
    def auditoria(self, obj):
        return '<a href="{}">Visualizar</a>'.format(
            reverse("candidato_history_psct", kwargs=dict(pk=obj.pk))
        )

    auditoria.short_description = "Auditoria"


admin.site.register(models.Candidato, CandidatoAdmin)
