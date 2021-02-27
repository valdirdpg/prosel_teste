from django.conf.urls import url
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.utils.safestring import mark_safe
from reversion import models
from reversion_compare.admin import CompareVersionAdmin


class PermissionCompareVersionAdmin(CompareVersionAdmin):
    @property
    def recover_permission(self):
        return f"psct.recover_{self.model._meta.model_name}"

    def compare_view(self, request, object_id, extra_context=None):

        if not request.user.has_perm(self.recover_permission):
            raise PermissionDenied()

        return super().compare_view(request, object_id, extra_context)

    def history_view(self, request, object_id, extra_context=None):

        if not request.user.has_perm(self.recover_permission):
            raise PermissionDenied()

        return super().history_view(request, object_id, extra_context)


class EntidadeFilter(admin.SimpleListFilter):

    title = "Entidade"
    parameter_name = "ate_o_mes"

    def lookups(self, request, model_admin):
        return [
            (c.id, c)
            for c in models.ContentType.objects.filter(app_label__in=["psct", "base"])
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(version__content_type=value).distinct()
        return queryset


class ReversionAdmin(admin.ModelAdmin):
    list_display = ("id", "date_created", "user", "resume", "view_changes")
    list_filter = (EntidadeFilter,)
    list_display_links = None
    date_hierarchy = "date_created"
    ordering = ("-date_created",)
    search_fields = ("user__username",)

    @mark_safe
    def view_changes(self, obj):
        return f'<a href="/admin/reversion/revision/{obj.id}/audit/">Visualizar</a>'

    view_changes.short_description = "Alterações"

    def resume(self, obj):
        return str(obj)

    resume.short_description = "Objetos alterados"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if obj:
            return False
        return super().has_change_permission(request, obj)

    def get_urls(self):
        """Returns the additional urls used by the Reversion admin."""
        urls = super().get_urls()
        admin_site = self.admin_site
        opts = self.model._meta
        info = (opts.app_label, opts.model_name)
        reversion_urls = [
            url(
                "^([^/]+)/audit/$",
                admin_site.admin_view(self.audit_view),
                name="psct_audit_view",
            )
        ]
        return reversion_urls + urls

    def audit_view(self, request, reversion):
        revision = get_object_or_404(models.Revision, pk=reversion)
        return render(request, "psct/audit.html", dict(revision=revision))


admin.site.register(models.Revision, ReversionAdmin)
