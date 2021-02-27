from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views import generic

from base.custom.autocomplete import auto_complete as ac
from base.custom.datatypes import BreadCrumb
from base.custom.views import ListView
from base.custom.views.decorators import column
from base.custom.views.mixin import AnyGroupRequiredMixin, GroupRequiredMixin
from psct.models.inscricao import Inscricao
from psct.views.recurso import ListGrupoPermissaoView


class DadosInscricaoView(GroupRequiredMixin, generic.TemplateView):
    raise_exception = True
    group_required = "CCA PSCT"
    template_name = "psct/prematricula/inscricao.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.inscricao = get_object_or_404(Inscricao, pk=self.kwargs["pk"])
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["inscricao"] = self.inscricao
        data["resultado"] = self.inscricao.get_resultado()
        data["situacao"] = self.inscricao.get_situacao()
        data["pontuacao"] = self.inscricao.get_extrato_pontuacao()
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_prematricula_psct")),
            ("Dados da Inscrição", ""),
        )
        return data


class ListCCAView(ListGrupoPermissaoView):
    group_name = "CCA PSCT"
    title_group = "Secretários CCA"


class ListInscricaoView(AnyGroupRequiredMixin, ListView):
    raise_exception = True
    group_required = ("Administradores PSCT", "CCA PSCT")
    paginate_by = 25
    show_numbers = True
    model = Inscricao
    list_display = ("candidato", "acoes")
    field_filters = ("curso__campus", "modalidade_cota")
    always_show_form = True

    autocomplete_fields = [
        ac("cursos.cursoselecao", "curso", ["curso__nome"]),
        ac("psct.candidato", "candidato", ["nome", "cpf", "user__username"]),
    ]

    def get_queryset(self):
        qs = super().get_queryset()
        return (
            qs.filter(
                resultados_preliminares__isnull=False,
                resultados_preliminares__resultado_curso__resultado__resultadofinal__isnull=False,
            )
            .order_by("candidato__nome")
            .distinct()
        )

    @mark_safe
    @column("Ações")
    def acoes(self, obj):
        return '<a href="{}">Visualizar</a>'.format(
            reverse("prematricula_inscricao_psct", kwargs=dict(pk=obj.pk))
        )

    def get_breadcrumb(self):
        return (("Inscrições", ""),)
