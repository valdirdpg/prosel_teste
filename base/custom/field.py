from django.db import models
from django.db.models import ForeignKey
from django.db.models.fields.reverse_related import ForeignObjectRel


def resolve_type(model_class, attribute_path):

    fields = attribute_path.split("__")
    field_obj = None

    for field in fields:
        field_obj = get_field(model_class, field)
        if isinstance(field_obj, models.ForeignKey):
            model_class = field_obj.related_model
        if isinstance(field_obj, ForeignObjectRel):
            model_class = field_obj.related_model
    return field_obj


def get_field(model_class, field):
    return model_class._meta.get_field(field)


def get_model_from_field(field):
    if isinstance(field, ForeignKey):
        return field.related_model
    if isinstance(field, ForeignObjectRel):
        return field.field.model
    return field.model


def get_verbose_name(model):
    if hasattr(model._meta, "verbose_name"):
        return model._meta.verbose_name
    return model.__name__.title()


def get_verbose_name_plural(model):
    if hasattr(model._meta, "verbose_name_plural"):
        return model._meta.verbose_name_plural
    return model.__name__.title()


def get_field_name(field):
    if hasattr(field, "verbose_name"):
        return field.verbose_name
    return field.name
