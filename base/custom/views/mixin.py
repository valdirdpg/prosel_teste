import operator
from functools import reduce

from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.safestring import mark_safe

from base.custom.permissions import user_in_group
from base.custom.views.decorators import column


class GroupRequiredMixin(AccessMixin):
    """
    CBV mixin which verifies that the current user belongs to specified group
    """

    group_required = None

    def get_group_required(self):
        """
        Override this method to override the group_required attribute.
        Must return an iterable.
        """
        if self.group_required is None:
            raise ImproperlyConfigured(
                "{0} is missing the group_required attribute. Define {0}.group_required, or override "
                "{0}.get_group_required().".format(self.__class__.__name__)
            )
        if isinstance(self.group_required, str):
            perms = (self.group_required,)
        else:
            perms = self.group_required
        return perms

    def has_permission(self):
        """
        Override this method to customize the way permissions are checked.
        """
        groups = self.get_group_required()
        return (
            self.request.user.groups.filter(name__in=groups).exists()
            or self.request.user.is_superuser
        )

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AnyGroupRequiredMixin(GroupRequiredMixin):
    def has_permission(self):
        """
        Override this method to customize the way permissions are checked.
        """
        groups = self.get_group_required()

        qs = reduce(operator.or_, [models.Q(name=g) for g in groups])

        return (
            self.request.user.groups.filter(qs).exists()
            or self.request.user.is_superuser
        )


class UserPermissionsListMixin:
    grupos_gerenciados = None
    list_display = ["usuario", "campi", "permissoes", "acoes"]
    model = User
    ordering = ["first_name", "last_name", "username"]
    show_permissions_column = True
    template_name = "reuse/listview.html"

    @column("Campi vinculados")
    def campi(self, obj):
        resultado = "-"
        campi = obj.lotacoes.all()
        if campi.exists():
            campi_li = ""
            for campus in campi:
                campi_li += f"<li>{campus}</li>"
            resultado = f"<ul>{campi_li}</ul>"
        return mark_safe(resultado)

    @column("Servidor")
    def usuario(self, obj):
        return f"{obj.get_full_name()} ({obj.username})"

    @column("Grupos de permissões")
    def permissoes(self, obj):
        grupos = "<ul>"
        for grupo in self.get_grupos_gerenciados():
            if user_in_group(obj, grupo):
                grupos += f"<li>{grupo}</li>"
        grupos += "</ul>"
        return mark_safe(grupos)

    def get_breadcrumb(self):
        return ((self.get_title(), ""),)

    def get_grupos_gerenciados(self):
        return self.grupos_gerenciados
