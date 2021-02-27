from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views import generic
from reversion.models import Revision, Version

from base.custom.datatypes import BreadCrumb
from base.custom.views import ListView
from base.custom.views.decorators import column
from base.custom.views.mixin import GroupRequiredMixin
from psct.models.candidato import Candidato
from psct.models.inscricao import Inscricao


class CandidatoHistoryView(GroupRequiredMixin, ListView):
    raise_exception = True
    model = Revision
    group_required = "Administradores PSCT"
    list_display = ("usuario", "data", "mudancas")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        return data

    def get_breadcrumb(self):
        return (
            ("Admin", reverse("admin:index")),
            ("Candidatos", reverse("admin:psct_candidato_changelist")),
            ("Histórico", ""),
        )

    @column("Usuário")
    def usuario(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.username})"
        return "-"

    @column("Data")
    def data(self, obj):
        return obj.date_created

    @mark_safe
    @column("Mudanças")
    def mudancas(self, obj):
        return '<a href="{}">Visualizar</a>'.format(
            reverse("revision_view_psct", kwargs=dict(pk=obj.pk))
        )

    def get_queryset(self):
        candidato = get_object_or_404(Candidato, pk=self.kwargs["pk"])
        return Revision.objects.filter(user=candidato.user)

    def get_title(self):
        return "Histórico de ações do candidato"


class InscricaoHistoryView(GroupRequiredMixin, ListView):
    raise_exception = True
    model = Revision
    group_required = "Administradores PSCT"
    list_display = ("usuario", "data", "mudancas")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        return data

    def get_breadcrumb(self):
        return (
            ("Admin", reverse("admin:index")),
            ("Inscrições", reverse("admin:psct_inscricao_changelist")),
            ("Histórico", ""),
        )

    @column("Usuário")
    def usuario(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.username})"
        return "-"

    @column("Data")
    def data(self, obj):
        return obj.date_created

    @mark_safe
    @column("Mudanças")
    def mudancas(self, obj):
        return '<a href="{}">Visualizar</a>'.format(
            reverse("revision_view_psct", kwargs=dict(pk=obj.pk))
        )

    def get_queryset(self):
        inscricao = get_object_or_404(Inscricao, pk=self.kwargs["pk"])
        ids = (
            Version.objects.get_for_object(inscricao)
            .values_list("revision_id")
            .distinct()
        )
        return Revision.objects.filter(id__in=ids)

    def get_title(self):
        return "Histórico de ações na inscrição"


class RevisionDetailView(GroupRequiredMixin, generic.DetailView):
    raise_exception = True
    model = Revision
    group_required = "Administradores PSCT"
    context_object_name = "revision"
    template_name = "psct/audit.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["breadcrumb"] = BreadCrumb.create(
            ("Admin", reverse("admin:index")), ("Dados do Registro de Auditoria", "")
        )
        return data
