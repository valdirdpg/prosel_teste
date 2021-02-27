from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe as mark_safe_decorator


def column(name, mark_safe=None):
    def decorator(function):
        function.short_description = name
        if mark_safe:
            return mark_safe_decorator(function)
        return function

    return decorator


def tab(name):
    def decorator(function):
        function.short_description = name
        return function

    return decorator


def menu(name, col=None, button_css=None):
    def decorator(function):

        column_name = col if col else name

        @wraps(function)
        @column(column_name)
        def new_function(self, obj):
            menu_class = self.get_menu_class()
            menu_obj = menu_class(name, button_css=button_css)
            function(self, menu_obj, obj)
            return menu_obj.render(self.request)

        return new_function

    return decorator


def group_required(group_name, login_url=None, raise_exception=False):
    def check_group(user):
        if user.is_superuser:
            return True

        if user.groups.filter(name=group_name).exists():
            return True
        # In case the 403 handler should be called raise the exception
        if raise_exception:
            raise PermissionDenied
        # As the last resort, show the login form
        return False

    return user_passes_test(check_group, login_url=login_url)
