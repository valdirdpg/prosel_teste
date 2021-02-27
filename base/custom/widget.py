import abc

from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class Item(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def render(self):
        raise NotImplementedError


class MenuItem(Item):
    def __init__(self, name, url):
        self.name = name
        self.url = url

    def render(self):
        return mark_safe(f'<li><a href="{self.url}">{self.name}</a></li>')

    def __eq__(self, other):
        return isinstance(other, MenuItem) and self.name == other.name and self.url == other.url

    def __repr__(self):
        return f"MenuItem (name={self.name}, url={self.url})"


class Separator(Item):
    def render(self):
        return mark_safe('<li role="separator" class="divider"></li>')

    def __eq__(self, other):
        return isinstance(other, Separator)


class Header(Item):
    def __init__(self, name):
        self.name = name

    def render(self):
        return mark_safe(f'<li class="dropdown-header">{self.name}</li>')

    def __eq__(self, other):
        return isinstance(other, Header) and self.name == other.name

    def __repr__(self):
        return f"Header (name={self.name})"


class Disabled(Item):
    def __init__(self, name):
        self.name = name

    def render(self):
        return mark_safe(f'<li class="disabled"><a href="#">{self.name}</a></li>')

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return f"Disabled (name={self.name})"


class SideBarMenu:
    counter_id = 0
    template_name = "base/dropdown_menu.html"

    def __init__(
        self, name, button_css="default", template_name=None, menu_css=None, **kwargs
    ):
        self.name = name
        self.button_css = button_css
        self.items = []
        self.extra_context = kwargs
        self.menu_css = menu_css
        if template_name:
            self.template_name = template_name
        self.id = self.get_new_id()

    @classmethod
    def increment_counter(cls):
        cls.counter_id += 1

    @classmethod
    def get_new_id(cls):
        cls.increment_counter()
        return cls.counter_id

    def render(self, request=None):
        context = {"menu": self}
        if self.extra_context:
            context.update(self.extra_context)
        return mark_safe(
            render_to_string(self.template_name, context=context, request=request)
        )

    def add_many(self, *items):
        self.items.extend([MenuItem(name, url) for (name, url) in items])

    def add(self, name, url):
        self.items.append(MenuItem(name, url))

    def add_separator(self):
        self.items.append(Separator())

    def add_header(self, name):
        self.items.append(Header(name))

    def add_disabled(self, name):
        self.items.append(Disabled(name))

    @property
    def empty(self):
        return not bool(self.items)
