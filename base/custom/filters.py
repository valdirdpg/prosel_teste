import abc

from ajax_select import fields as ajax_fields
from django import forms
from django.db import models
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.template.loader import render_to_string

from base.custom import field


class Filter(metaclass=abc.ABCMeta):
    template_name = "psct/base/custom/filter.html"

    title = None
    parameter_name = None

    def __init__(self, request):
        self.request = request

    @abc.abstractmethod
    def get_choices(self, queryset):
        raise NotImplementedError

    @abc.abstractmethod
    def get_queryset(self, queryset):
        raise NotImplementedError

    def get_value(self):
        return self.request.GET.get(self.parameter_name)

    def has_output(self):
        return bool(self.get_choices())

    def get_expected_parameters(self):
        return [self.parameter_name]

    def render(self):
        return render_to_string(self.template_name, context=self.get_context_data())

    def get_context_data(self):
        return dict(filter=self)

    def get_form_field(self, queryset):
        return forms.ChoiceField(
            label=self.title, required=False, choices=self.get_choices(queryset)
        )


class TypedFieldFilter(metaclass=abc.ABCMeta):
    priority = 1
    has_custom_queryset = False

    def __init__(self, field, request):
        self.field = field
        self.request = request

    @classmethod
    @abc.abstractmethod
    def match(cls, obj, request):
        raise NotImplementedError

    @abc.abstractmethod
    def get_choices(self, queryset):
        raise NotImplementedError

    @abc.abstractmethod
    def get_title(self):
        raise NotImplementedError

    def get_queryset(self, field_path, value, queryset):
        raise NotImplementedError


class FieldFilter(Filter):
    _register = []

    def __init__(self, model, field_path, request):
        super().__init__(request)
        self.field_path = field_path
        self.model = model
        self.field = field.resolve_type(self.model, self.field_path)
        self.filter = self.get_typed_filter()
        self.parameter_name = self.field.name
        if self.filter:
            self.title = self.filter.get_title()
        else:
            self.title = self.field.verbose_name.title()

    def get_choices(self, queryset):
        if self.filter:
            return self.filter.get_choices(queryset)
        try:
            return self.field.get_choices()
        except AttributeError:
            return [
                (v, v)
                for v in queryset.values_list(self.field_path, flat=True).distinct()
            ]

    def get_queryset(self, queryset):
        value = self.get_value()
        if value:
            if self.filter and self.filter.has_custom_queryset:
                return self.filter.get_queryset(
                    self.field_path, value, queryset
                ).distinct()
            return queryset.filter(**{self.field_path: value}).distinct()
        return queryset

    @classmethod
    def register(cls, typed_field_filter):
        cls._register.append(typed_field_filter)
        return typed_field_filter

    def get_typed_filter(self):
        filters = sorted(self._register, key=lambda x: x.priority)
        for filter_ in filters:
            if filter_.match(self.field, self.request):
                return filter_(self.field, self.request)


@FieldFilter.register
class RelatedObjectField(TypedFieldFilter):
    @classmethod
    def match(cls, obj, request):
        return isinstance(obj, ForeignObjectRel)

    def get_title(self):
        return field.get_verbose_name(self.field.related_model)

    def get_choices(self, queryset):
        return self.field.get_choices()


@FieldFilter.register
class BooleanFieldFilter(TypedFieldFilter):
    @classmethod
    def match(cls, obj, request):
        return isinstance(obj, models.BooleanField)

    def get_title(self):
        return self.field.verbose_name

    def get_choices(self, queryset):
        return [("", "---------"), ("0", "Não"), ("1", "Sim")]


class AutoCompleteFilter(Filter):
    def __init__(self, view, lookup):
        super().__init__(view.request)
        self.lookup = lookup
        self.view = view
        self.parameter_name = "autocomplete_" + self.lookup.model.__name__.lower()
        if lookup.title:
            self.title = lookup.title
        else:
            self.title = field.get_verbose_name(lookup.model)
        self.check_field_path(self.lookup.field_path)

    def check_field_path(self, path):
        field_obj = field.resolve_type(self.view.model, path)
        if not isinstance(field_obj, (models.ForeignKey, ForeignObjectRel)):
            raise ValueError("'field_path' must pointer to a model, not field.")

    def get_choices(self, queryset):
        return []

    def get_form_field(self, queryset):
        return ajax_fields.AutoCompleteSelectField(
            self.lookup.get_channel_name(),
            help_text="",
            label=self.title,
            required=False,
        )

    def get_queryset(self, queryset):
        value = self.get_value()
        if value:
            return queryset.filter(**{self.lookup.field_path: value}).distinct()
        return queryset
