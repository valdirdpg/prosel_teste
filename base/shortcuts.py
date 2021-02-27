from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404


def get_object_or_permission_denied(klass, **kwargs):
    try:
        return get_object_or_404(klass, **kwargs)
    except Http404:
        raise PermissionDenied
