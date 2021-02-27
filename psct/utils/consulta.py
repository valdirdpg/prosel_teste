from functools import partial

from django.db import models

from base.custom import field
from psct.dbfields import DocumentFileField

CACHE_TYPE = {}


def format_type_function(field_type):
    function = CACHE_TYPE.get(field_type.__class__)
    if function:
        return partial(function, field_type)
    return None


def get_format(model_class, query_string):
    type_ref = field.resolve_type(model_class, query_string)
    return format_type_function(type_ref)


def register(field):
    def register_wraps(function):
        if field not in CACHE_TYPE:
            CACHE_TYPE[field] = function
        else:
            raise ValueError("Função de format já registrada")
        return function

    return register_wraps


@register(DocumentFileField)
def format_link(type_ref, obj):
    return f'<a href="/media/{obj}/">Visualizar</a>'


@register(models.ForeignKey)
def format_link(type_ref, obj):
    if obj is None:
        return "--"
    model_class = type_ref.related_model
    return str(model_class.objects.get(id=obj))


@register(models.OneToOneRel)
def format_one_to_one(type_ref, obj):
    if obj is None:
        return "--"
    model_class = type_ref.related_model
    return str(model_class.objects.get(id=obj))
