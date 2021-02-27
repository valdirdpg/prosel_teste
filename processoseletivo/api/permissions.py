from django.core.exceptions import ImproperlyConfigured
from rest_framework import permissions


class IsMemberOfGroup(permissions.BasePermission):
    def has_permission(self, request, view):
        if hasattr(view, "group_required"):
            groups = self.get_group_required(view)
            return (
                request.user.groups.filter(name__in=groups).exists()
                or request.user.is_superuser
            )
        return False

    def get_group_required(self, view):
        """
        Override this method to override the group_required attribute.
        Must return an iterable.
        """
        if view.group_required is None:
            raise ImproperlyConfigured(
                "{0} is missing the group_required attribute. Define {0}.group_required, or override "
                "{0}.get_group_required().".format(self.__class__.__name__)
            )
        if isinstance(view.group_required, str):
            perms = (view.group_required,)
        else:
            perms = view.group_required
        return perms
