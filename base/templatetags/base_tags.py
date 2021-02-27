import re
import uuid

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from ifpb_django_permissions.perms import in_any_groups

from base import utils
from base.custom.utils import get_query_string
from cursos.models import Campus
from processoseletivo.models import ProcessoSeletivo, Recurso

register = template.Library()


@register.simple_tag
def url_replace(request, field, value, *args):
    """
    Ajusta os valores do parâmetro GET
    :param request:
    :param field: nome do parâmetro
    :param value: valor do parâmetro
    :param args: parâmetros a serem excluídos do GET
    :return: lista de parâmetros atualizada.
    """
    dict_ = request.GET.copy()

    for arg in args:
        dict_.pop(arg, None)

    if value:
        dict_[field] = value
    else:
        if field in dict_:
            dict_.pop(field, None)
    return dict_.urlencode()


@register.simple_tag
def get_processos_seletivos():
    return ProcessoSeletivo.objects.all()


@register.simple_tag
def get_campis():
    return Campus.objects.all().order_by("nome")


@register.simple_tag
def has_recursos(candidato_id):
    return Recurso.objects.filter(
        analise_documental__confirmacao_interesse__inscricao__candidato__id=candidato_id,
        analise_documental__confirmacao_interesse__etapa__encerrada=False,
    ).exists()


@register.filter
def highlight(text, sterm):
    patern = r"({})".format(str(re.escape(sterm)))
    result = re.sub(patern, r"<mark>\1</mark>", str(text), flags=re.IGNORECASE)
    return mark_safe(result)


@register.filter
def file_extension(file):
    return utils.file_extension(file)


@register.filter
def format_name(user):
    if user.first_name or user.last_name:
        return user.get_full_name()
    return f"{user}"


class RenderBox(template.Node):
    def __init__(self, nodelist, titulo, opened, boxid):
        self.nodelist = nodelist
        self.titulo = titulo[1:-1]
        self.boxid = boxid
        self.opened = template.Variable(opened)

    def render(self, context):
        return render_to_string(
            "base/box.html",
            dict(
                titulo=self.get_value(self.titulo, context),
                boxid=self.boxid if self.boxid else uuid.uuid4().hex,
                conteudo=self.nodelist.render(context),
                opened=self.opened.resolve(context),
            ),
        )

    @staticmethod
    def get_value(var, context):
        return template.Template(var).render(template.Context(context))


@register.tag(name="box")
def box(parser, token):
    nodelist = parser.parse(("endbox",))
    tag, *params = token.split_contents()
    tamanho = len(params)
    boxid, titulo, css, opened = None, None, None, "False"

    if tamanho == 1:
        titulo = params[0]
    elif tamanho == 2:
        titulo, opened = params
    elif tamanho == 3:
        titulo, opened, boxid = params

    parser.delete_first_token()
    return RenderBox(nodelist, titulo, opened, boxid)


@register.simple_tag
def get_object_columns(view, obj):
    return view.get_object_columns(obj)


@register.simple_tag
def get_active_tab_tag(actual_tab, tab_name, loop_index):
    if loop_index == 0 and not actual_tab:
        return True
    return actual_tab == tab_name


@register.simple_tag
def get_tab_url(request, tab_name):
    query_string = get_query_string(
        request.GET, new_params={"tab": tab_name}, remove=["page"]
    )
    return f"{request.META['PATH_INFO']}{query_string}"


@register.simple_tag
def apply_show_number(view, number, page=1):
    if page in [None, ""]:
        page = 1

    total_number = view.paginate_by * (int(page) - 1) + number
    return view.number_display(total_number)


@register.simple_tag
def user_in_groups(user, *groups):
    return in_any_groups(user, groups)
