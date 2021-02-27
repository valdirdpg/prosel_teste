import operator
from functools import reduce

from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.http import Http404
from django.views import generic

from base.custom import field as m_field
from base.custom.datatypes import BreadCrumb
from base.custom.filters import AutoCompleteFilter, FieldFilter
from base.custom.permissions import ProfileChecker
from base.custom.widget import SideBarMenu
from base.forms import Form


class ListViewForm(Form):
    field_class = "form-control filter-form"

    def __init__(self, view, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if view.has_tabs():
            self.fields["tab"] = forms.CharField(
                widget=forms.HiddenInput,
                initial=view.request.GET.get("tab"),
                required=False,
            )

        qs = view.get_queryset()
        for filter_ in view.get_filters():
            self.fields[filter_.parameter_name] = filter_.get_form_field(qs)
            initial = view.request.GET.get(filter_.parameter_name)
            if initial:
                self.fields[filter_.parameter_name].initial = initial

        if view.get_search_fields():
            self.fields["q"] = forms.CharField(
                label="Busca", initial=view.request.GET.get("q"), required=False
            )
        self.styled_fields = ["__all__"]
        self.apply_style()


def get_method_name(method):
    if hasattr(method, "short_description"):
        return method.short_description
    return method.__name__.title()


class Column:
    def __init__(self, attribute_name, view):
        self.name = self.resolve_name(attribute_name, view)

    @staticmethod
    def resolve_name(attribute_name, view):
        try:
            field = m_field.resolve_type(view.model, attribute_name)
            return m_field.get_field_name(field)
        except FieldDoesNotExist:
            method = getattr(view, attribute_name, None)
            if method:
                return get_method_name(method)
            raise AttributeError(
                f"'{attribute_name}' is not atribute of {view.model} or {view.__class__}"
            )

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name


class ObjectData:
    def __init__(self, view, obj):
        self.view = view
        self.obj = obj

    def get_field_value(self, field_name):
        return getattr(self.obj, field_name)

    def get_method_value(self, method_name):
        method = getattr(self.view, method_name)
        return method(self.obj)

    def get_column_value(self, name):
        try:
            return self.get_field_value(name)
        except AttributeError:
            try:
                return self.get_method_value(name)
            except AttributeError as error:
                raise AttributeError(
                    f"'{name}' is not atribute of {self.obj.__class__} or {self.view.__class__}"
                ) from error

    def __iter__(self):
        list_display = self.view.get_list_display()
        if list_display:
            for column in list_display:
                yield self.get_column_value(column)
        else:
            yield self.obj


class ListView(generic.ListView):
    template_name = "base/listview.html"
    simple_filters = []
    field_filters = []
    list_display = []
    form_factory = None
    paginate_by = 25
    tabs = []
    search_fields = []
    autocomplete_fields = []
    menu_class = SideBarMenu
    profile_checker = None
    show_numbers = False
    always_show_form = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cache_queryset = None
        self._filters_cache = None

    def get_autocomplete_fields(self):
        return self.autocomplete_fields

    def has_autocomplete_fields(self):
        return bool(self.autocomplete_fields)

    def get_search_fields(self):
        return tuple(self.search_fields)

    def has_search_fields(self):
        return bool(self.get_search_fields())

    def get_list_display(self):
        return tuple(self.list_display)

    def get_columns(self):
        list_display = self.get_list_display()
        return [self.get_column(name) for name in list_display]

    def get_column(self, name):
        return Column(name, self)

    def get_object_columns(self, obj):
        return ObjectData(self, obj)

    def get_simple_filters(self):
        return tuple(self.simple_filters)

    def get_field_filters(self):
        return tuple(self.field_filters)

    def has_filter(self):
        return bool(self.get_filters())

    def get_filters(self):
        if not self._filters_cache:
            simple_filters = [
                filter_class(self.request) for filter_class in self.get_simple_filters()
            ]
            field_filters = [
                FieldFilter(self.model, field_path, self.request)
                for field_path in self.get_field_filters()
            ]
            autocomplete_filters = [
                AutoCompleteFilter(self, config)
                for config in self.get_autocomplete_fields()
            ]
            self._filters_cache = simple_filters + field_filters + autocomplete_filters
        return self._filters_cache

    def has_any_filter_set(self):
        for filter_ in self.get_filters():
            if filter_.get_value():
                return True
        return self._requires_search_query()

    def get_always_show_form(self):
        return self.always_show_form

    def should_display_form(self):
        return self.has_any_filter_set() or self.get_always_show_form()

    def _get_queryset(self):
        if not self._cache_queryset:
            queryset = super().get_queryset()
            filters = self.get_filters()
            for filter_ in filters:
                queryset = filter_.get_queryset(queryset)
            if self._requires_search_query():
                queryset = queryset.filter(self._construct_search_query())
            self._cache_queryset = queryset.distinct()
        return self._cache_queryset

    def _requires_search_query(self):
        return self.has_search_fields() and self.request.GET.get("q")

    def _construct_search_query(self):
        q = self.request.GET["q"]

        def get_q(field_name):
            field = m_field.resolve_type(self.model, field_name)
            name = field_name
            if isinstance(field, (models.CharField, models.TextField)):
                name += "__unaccent"
            name = f"{name}__icontains"
            return reduce(operator.and_, [models.Q(**{name: p}) for p in q.split()])

        return reduce(
            operator.or_, [get_q(field_name) for field_name in self.get_search_fields()]
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = self.get_title()
        data["view"] = self
        if self.has_filter() or self.has_search_fields():
            form = ListViewForm(self)
            data["form"] = form

        breadcrumb = self.get_breadcrumb()
        if breadcrumb:
            data["breadcrumb"] = BreadCrumb.create(*breadcrumb)
        return data

    def get_title(self):
        return m_field.get_verbose_name_plural(self.model)

    def get_tabs(self):
        return tuple(self.tabs)

    def has_tabs(self):
        return bool(self.get_tabs())

    def get_tab_queryset(self, tab):
        method = getattr(self, tab)
        return method(self._get_queryset())

    def get_tab_names(self):
        return [(name, self._get_method_name(name)) for name in self.get_tabs()]

    def _get_method_name(self, name):
        method = getattr(self, name)
        return get_method_name(method)

    def get_tab(self):
        tab = self.request.GET.get("tab")
        if tab and tab not in self.get_tabs():
            raise Http404()
        return tab if tab else self.get_tabs()[0]

    def get_queryset(self):
        tabs = self.get_tabs()
        if tabs:
            tab = self.get_tab()
            return self.get_tab_queryset(tab)
        return self._get_queryset()

    def get_menu_class(self):
        return self.menu_class

    def get_button_area(self):
        return []

    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        if self.profile_checker:
            self.profile = ProfileChecker(request.user, self.profile_checker)
        return super().dispatch(request, *args, **kwargs)

    def get_number_label(self):
        return "#"

    def get_show_numbers(self):
        return self.show_numbers

    def number_display(self, number):
        return number

    def get_breadcrumb(self):
        pass
