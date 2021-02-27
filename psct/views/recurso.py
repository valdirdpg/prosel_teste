from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import models as dj_models
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views import generic
from reversion.views import RevisionMixin
from suaprest.django import SUAPDjangoClient as Client

from base.custom.autocomplete import auto_complete as ac
from base.custom.datatypes import BreadCrumb
from base.custom.views import ListView
from base.custom.views.decorators import column, menu, tab
from base.custom.views.mixin import AnyGroupRequiredMixin, GroupRequiredMixin
from base.custom.widget import SideBarMenu
from base.shortcuts import get_object_or_permission_denied
from editais.models import Edital
from monitoring.models import Job
from psct.distribuicao.recurso import (
    RedistribuirRecursoAvaliador,
    RedistribuirRecursoHomologador,
)
from psct.filters import recurso as filters
from psct.forms import recurso as forms
from psct.models import recurso as models
from psct.models.consulta import Coluna
from psct.tasks.recurso import distribuir_recursos, generate_resultado_recursos_pdf
from psct.utils import recurso as utils
from .. import permissions


class RecursoCreateView(RevisionMixin, UserPassesTestMixin, generic.CreateView):
    raise_exception = True
    model = models.Recurso
    form_class = forms.RecursoForm
    template_name = "psct/base/display_form.html"

    def test_func(self):

        if not self.request.user.is_authenticated:
            return False

        self.fase = get_object_or_404(models.FaseRecurso, pk=self.kwargs["fase_pk"])
        self.inscricao = get_object_or_permission_denied(
            models.Inscricao, edital=self.fase.edital, candidato__user=self.request.user
        )
        has_recurso = (
            models.Recurso.objects.filter(
                fase=self.fase, inscricao__candidato__user=self.request.user
            )
            .distinct()
            .exists()
        )
        if self.fase.em_periodo_submissao and not has_recurso:
            return True
        return False

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        initial = kwargs.get("initial")
        if initial is not None:
            initial.update(
                fase=self.fase, usuario=self.request.user, inscricao=self.inscricao
            )
        return kwargs

    def get_success_url(self):
        messages.info(self.request, "Recurso cadastrado com sucesso")
        return reverse("list_recurso_psct")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Novo Recurso"
        data["nome_botao"] = "Salvar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Minhas Inscrições", reverse("index_psct")),
            ("Recursos", reverse("list_recurso_psct")),
            ("Novo Recurso", ""),
        )
        return data


class RecursoUpdateView(RevisionMixin, UserPassesTestMixin, generic.UpdateView):
    raise_exception = True
    model = models.Recurso
    form_class = forms.RecursoForm
    template_name = "psct/base/display_form.html"

    def test_func(self):
        self.object = self.get_object()
        return (
            self.object.usuario == self.request.user
            and self.object.fase.em_periodo_submissao
        )

    def get_success_url(self):
        messages.info(self.request, "Recurso atualizado com sucesso")
        return reverse("view_recurso_psct", kwargs=dict(pk=self.object.pk))

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Editar Recurso"
        data["nome_botao"] = "Atualizar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Minhas Inscrições", reverse("index_psct")),
            ("Recursos", reverse("list_recurso_psct")),
            ("Editar Recurso", ""),
        )
        return data


class GrupoCreateView(GroupRequiredMixin, generic.FormView):
    raise_exception = True
    group_required = "Administradores PSCT"
    form_class = forms.RecursoGrupoForm
    template_name = "psct/base/display_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        initial = kwargs.get("initial")
        if initial is not None:
            initial.update(edital=self.kwargs["edital_pk"])
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Novo Grupo"
        data["nome_botao"] = "Salvar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Grupos", reverse("list_grupo_psct")), ("Novo Grupo", "")
        )
        return data

    def form_valid(self, form):
        models.create_grupo_recurso(
            self.edital,
            form.cleaned_data["nome"],
            form.cleaned_data["servidores"],
            form.cleaned_data["grupos_merge"],
            form.cleaned_data["grupos_exclude"],
        )
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        self.edital = get_object_or_404(Edital, pk=self.kwargs["edital_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.info(self.request, "Grupo criado com sucesso")
        return reverse("list_grupo_psct")


class GrupoUpdateView(GroupRequiredMixin, generic.FormView):
    raise_exception = True
    group_required = "Administradores PSCT"
    form_class = forms.UpdateRecursoGrupoForm
    template_name = "psct/base/display_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        initial = kwargs.get("initial")
        initial.update(
            nome=self.grupo_edital.grupo.name,
            servidores=[u.username for u in self.grupo_edital.grupo.user_set.all()],
            edital=self.grupo_edital.edital,
        )
        kwargs["is_update"] = True
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Atualizar Grupo"
        data["nome_botao"] = "Atualizar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Grupos", reverse("list_grupo_psct")), ("Atualizar Grupo", "")
        )
        return data

    def form_valid(self, form):
        models.update_grupo_recurso(
            self.grupo_edital.grupo,
            form.cleaned_data["nome"],
            form.cleaned_data["servidores"],
            form.cleaned_data["grupos_merge"],
            form.cleaned_data["grupos_exclude"],
        )
        self.grupo_edital.edital = form.cleaned_data["edital"]
        self.grupo_edital.save()
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        self.grupo_edital = get_object_or_404(
            models.GrupoEdital, pk=self.kwargs["grupoedital_pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.info(self.request, "Grupo atualizado com sucesso")
        return reverse("list_grupo_psct")


class AgruparRecursoView(GroupRequiredMixin, generic.FormView):
    raise_exception = True
    group_required = "Administradores PSCT"
    form_class = forms.AgruparRecursoForm
    template_name = "psct/base/display_form.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Agrupar Recursos para Distribuição"
        data["nome_botao"] = "Selecionar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")), ("Agrupar Recursos", "")
        )
        return data

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.fase = get_object_or_404(models.FaseRecurso, pk=self.kwargs["fase_pk"])
            return (
                self.fase.data_encerramento_submissao
                < datetime.now()
                < self.fase.data_inicio_analise
            )
        return perm

    def form_valid(self, form):
        self.coluna = form.cleaned_data["criterio"]
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "distribuir_recurso_psct",
            kwargs=dict(fase_pk=self.kwargs["fase_pk"], coluna_pk=self.coluna.pk),
        )


class DistribuirRecursoView(GroupRequiredMixin, generic.FormView):
    raise_exception = True
    group_required = "Administradores PSCT"
    form_class = forms.DistribuirRecursoForm
    template_name = "psct/base/display_form.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.fase = get_object_or_404(models.FaseRecurso, pk=self.kwargs["fase_pk"])
            self.coluna = get_object_or_404(Coluna, pk=self.kwargs["coluna_pk"])
            return (
                self.fase.data_encerramento_submissao
                < datetime.now()
                < self.fase.data_inicio_analise
            )
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Distribuir Recurso"
        data["nome_botao"] = "Distribuir"
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")),
            (
                "Agrupar Recursos",
                reverse(
                    "agrupar_recurso_psct", kwargs=dict(fase_pk=self.kwargs["fase_pk"])
                ),
            ),
            ("Distribuir Recursos", ""),
        )
        return data

    def form_valid(self, form):
        async_result = form.distribuir()
        self.job = Job.new(
            self.request.user, async_result, name=distribuir_recursos.name
        )
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["coluna"] = self.coluna
        kwargs["fase"] = self.fase
        return kwargs

    def get_success_url(self):
        messages.info(
            self.request,
            "Os recursos estão sendo distribuídos entre os grupos e usuários",
        )
        return self.job.get_absolute_url()


class RecursoAdminView(GroupRequiredMixin, generic.DetailView):
    raise_exception = True
    group_required = "Administradores PSCT"
    model = models.Recurso
    template_name = "psct/recurso/adminview.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")), ("Recurso", "")
        )
        return data


class CreateParecerAvaliadorView(RevisionMixin, GroupRequiredMixin, generic.CreateView):
    raise_exception = True
    model = models.ParecerAvaliador
    group_required = "Avaliador PSCT"
    template_name = "psct/recurso/pareceravaliador.html"
    form_class = forms.ParecerAvaliadorForm

    def has_permission(self):
        perm = super().has_permission()
        self.recurso = get_object_or_404(models.Recurso, pk=self.kwargs["pk"])

        if self.recurso.pareceres_avaliadores.filter(
            avaliador=self.request.user
        ).exists():
            return False

        if not self.recurso.fase.em_periodo_analise:
            return False

        if perm:
            return self.request.user.mailbox_avaliador.filter(
                recursos=self.kwargs["pk"]
            )
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["recurso"] = self.recurso
        data["titulo"] = "Novo Parecer"
        data["nome_botao"] = "Salvar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")), ("Novo Parecer", "")
        )
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        initial = kwargs.get("initial")
        initial.update(recurso=self.recurso, avaliador=self.request.user)
        return kwargs

    def get_success_url(self):
        messages.info(self.request, "Parecer cadastrado com sucesso")
        if self.object.concluido:
            return reverse("list_recurso_psct")
        else:
            return reverse("list_recurso_psct") + "?tab=em_avaliacao"


class UpdateParecerAvaliadorView(RevisionMixin, GroupRequiredMixin, generic.UpdateView):
    raise_exception = True
    model = models.ParecerAvaliador
    group_required = "Avaliador PSCT"
    template_name = "psct/recurso/pareceravaliador.html"
    form_class = forms.ParecerAvaliadorForm

    def has_permission(self):
        perm = super().has_permission()
        self.object = get_object_or_404(
            models.ParecerAvaliador, pk=self.kwargs["pk"], concluido=False
        )
        if not self.object.recurso.fase.em_periodo_analise:
            return False
        if perm:
            return self.object.avaliador == self.request.user
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["recurso"] = self.object.recurso
        data["titulo"] = "Editar Parecer"
        data["nome_botao"] = "Atualizar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")), ("Atualizar Parecer", "")
        )
        return data

    def get_success_url(self):
        messages.info(self.request, "Parecer atualizado com sucesso")
        if self.object.concluido:
            return reverse("list_recurso_psct")
        else:
            return reverse("list_recurso_psct") + "?tab=em_avaliacao"


class CreateParecerHomologadorView(
    RevisionMixin, GroupRequiredMixin, generic.CreateView
):
    raise_exception = True
    model = models.ParecerHomologador
    group_required = "Homologador PSCT"
    template_name = "psct/recurso/parecerhomologador.html"
    form_class = forms.ParecerHomologadorForm

    def has_permission(self):
        perm = super().has_permission()

        if perm:
            self.recurso = get_object_or_404(models.Recurso, pk=self.kwargs["pk"])

            if (
                self.recurso.pareceres_avaliadores.count()
                != self.recurso.fase.quantidade_avaliadores
            ):
                return False

            if self.recurso.pareceres_homologadores.filter(
                homologador=self.request.user
            ).exists():
                return False

            if not self.recurso.fase.em_periodo_analise:
                return False

            return self.request.user.mailbox_homologador.filter(
                recursos=self.kwargs["pk"]
            )
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["recurso"] = self.recurso
        data["titulo"] = "Novo Parecer"
        data["nome_botao"] = "Salvar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")), ("Novo Parecer", "")
        )
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        initial = kwargs.get("initial")
        initial.update(recurso=self.recurso, homologador=self.request.user)
        return kwargs

    def get_success_url(self):
        messages.info(self.request, "Parecer cadastrado com sucesso")
        return reverse("list_recurso_psct") + "?tab=homologados"


class UpdateParecerHomologadorView(
    RevisionMixin, GroupRequiredMixin, generic.UpdateView
):
    raise_exception = True
    model = models.ParecerHomologador
    group_required = "Homologador PSCT"
    template_name = "psct/recurso/parecerhomologador.html"
    form_class = forms.ParecerHomologadorForm

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.object = get_object_or_404(
                models.ParecerHomologador, pk=self.kwargs["pk"]
            )
            if not self.object.recurso.fase.em_periodo_analise:
                return False
            return self.object.homologador == self.request.user
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["recurso"] = self.object.recurso
        data["titulo"] = "Editar Parecer"
        data["nome_botao"] = "Atualizar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")), ("Atualizar Parecer", "")
        )
        return data

    def get_success_url(self):
        messages.info(self.request, "Parecer atualizado com sucesso")
        return reverse("list_recurso_psct") + "?tab=homologados"


class RecursoView(GroupRequiredMixin, generic.DetailView):
    group_required = "Candidatos PSCT"
    raise_exception = True
    model = models.Recurso
    template_name = "psct/recurso/recurso_detail.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.object = self.get_object()
            return self.object.usuario == self.request.user
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        menu = SideBarMenu("Opções", menu_css="pull-right", button_css="success")
        if self.object.fase.em_periodo_submissao:
            menu.add(
                "Editar", reverse("change_recurso_psct", kwargs=dict(pk=self.object.id))
            )
        data["menu"] = menu
        aid = self.object.id
        data["breadcrumb"] = BreadCrumb.create(
            ("Minhas Inscrições", reverse("index_psct")),
            ("Recursos", reverse("list_recurso_psct")),
            (f"Recurso #{aid}", ""),
        )
        return data


class ListRecursoView(AnyGroupRequiredMixin, ListView):
    group_required = (
        "Candidatos PSCT",
        "Avaliador PSCT",
        "Homologador PSCT",
        "Administradores PSCT",
    )
    raise_exception = True
    simple_filters = [filters.EditalPSCTFilter]
    field_filters = ("inscricao__curso__campus",)
    list_display = ("id", "candidato", "curso", "fase", "acoes")
    tabs = [
        "meus",  # candidato
        "nao_avaliados",
        "em_avaliacao",
        "entregues",  # avaliador
        "aguardando_avaliacao",
        "aguardando_homologacao",
        "homologados",  # homologação
        "todos",
    ]
    autocomplete_fields = [
        ac("cursos.cursoselecao", "inscricao__curso", ["curso__nome"]),
        ac("psct.candidato", "inscricao__candidato", ["nome", "cpf", "user__username"]),
    ]
    model = models.Recurso
    profile_checker = [
        ("avaliador", "Avaliador PSCT"),
        ("homologador", "Homologador PSCT"),
        ("candidato", "Candidato PSCT"),
        ("administrador", "Administradores PSCT"),
    ]

    @column("Curso")
    def curso(self, obj):
        return f"{obj.inscricao.curso.formacao} em {obj.inscricao.curso.curso.nome}"

    @column("Candidato")
    def candidato(self, obj):
        return obj.inscricao.candidato

    @mark_safe
    @column("Situação")
    def situacao(self, obj: models.Recurso):
        if not obj.pode_ver_parecer:
            return '<span class="status status-pendente">Aguardando Parecer</span>'
        else:
            parecer = obj.pareceres_homologadores.first()
            if parecer and parecer.aceito:
                return '<span class="status status-deferido">Deferido</span>'
            return '<span class="status status-indeferido">Indeferido</span>'

    @mark_safe
    @column("Situação")
    def situacao_admin(self, obj: models.Recurso):
        status, css = "Indisponível", "pendente"

        def span(status_, css_):
            return f'<span class="status status-{css_}">{status_}</span>'

        if not obj.mailbox_avaliadores.exists():
            status, css = "Sem Avaliadores", "pendente"
            return span(status, css)
        if (
            obj.mailbox_avaliadores.exists()
            and obj.mailbox_avaliadores.count() != obj.fase.quantidade_avaliadores
        ):
            status, css = "Avaliadores Incompletos", "pendente"
            return span(status, css)
        if obj.pareceres_avaliadores.count() != obj.fase.quantidade_avaliadores:
            status, css = "Com Avaliação Pendente", "pendente"
            return span(status, css)
        if (
            obj.pareceres_avaliadores.filter(concluido=True).count()
            != obj.fase.quantidade_avaliadores
        ):
            status, css = "Com Avaliação Não Concluída", "pendente"
            return span(status, css)
        if not obj.mailbox_homologadores.exists():
            status, css = "Sem homologador", "pendente"
            return span(status, css)
        if (
            obj.pareceres_avaliadores.filter(concluido=True).count()
            == obj.fase.quantidade_avaliadores
            and obj.mailbox_homologadores.exists()
            and not obj.pareceres_homologadores.exists()
        ):
            status, css = "Aguardando Homologador", "pendente"
            return span(status, css)
        if obj.pareceres_homologadores.filter(aceito=True).exists():
            status, css = "Deferida", "deferido"
            return span(status, css)
        if obj.pareceres_homologadores.filter(aceito=False).exists():
            status, css = "Indeferida", "indeferido"
            return span(status, css)
        return span(status, css)

    @menu("Opções", col="Ações")
    def acoes(self, menu_obj: ListView.menu_class, obj: models.Recurso) -> None:
        if self.user == obj.usuario:
            menu_obj.add(
                "Visualizar", reverse("view_recurso_psct", kwargs=dict(pk=obj.pk))
            )
            if obj.pode_ver_parecer and obj.pareceres_homologadores.exists():
                menu_obj.add(
                    "Visualizar Parecer",
                    reverse("view_parecer_psct", kwargs=dict(pk=obj.parecer.pk)),
                )
        if obj.fase.em_periodo_submissao and obj.usuario == self.user:
            menu_obj.add(
                "Editar", reverse("change_recurso_psct", kwargs=dict(pk=obj.pk))
            )
        if self.profile.is_avaliador:
            if self.user.mailbox_avaliador.filter(recursos=obj):
                parecer = obj.pareceres_avaliadores.filter(avaliador=self.user).first()
                if not parecer:
                    if obj.fase.em_periodo_analise:
                        menu_obj.add(
                            "Emitir Parecer",
                            reverse(
                                "add_parecer_avaliador_psct", kwargs=dict(pk=obj.pk)
                            ),
                        )
                else:
                    if not parecer.concluido:
                        if obj.fase.em_periodo_analise:
                            menu_obj.add(
                                "Alterar Parecer",
                                reverse(
                                    "change_parecer_avaliador_psct",
                                    kwargs=dict(pk=parecer.pk),
                                ),
                            )
                    else:
                        menu_obj.add(
                            "Visualizar Parecer",
                            reverse(
                                "view_parecer_avaliador_psct",
                                kwargs=dict(pk=parecer.pk),
                            ),
                        )

        if self.profile.is_homologador and obj.homologador_pode_emitir_parecer:
            if self.user.mailbox_homologador.filter(recursos=obj):
                parecer = obj.pareceres_homologadores.filter(
                    homologador=self.user
                ).first()
                if not parecer:
                    if obj.fase.em_periodo_analise:
                        menu_obj.add(
                            "Emitir Parecer",
                            reverse(
                                "add_parecer_homologador_psct", kwargs=dict(pk=obj.pk)
                            ),
                        )
                else:
                    if obj.fase.em_periodo_analise:
                        menu_obj.add(
                            "Alterar Parecer",
                            reverse(
                                "change_parecer_homologador_psct",
                                kwargs=dict(pk=parecer.pk),
                            ),
                        )
                    menu_obj.add(
                        "Visualizar Parecer",
                        reverse(
                            "view_parecer_homologador_psct", kwargs=dict(pk=parecer.pk)
                        ),
                    )
        if self.profile.is_administrador:
            menu_obj.add(
                "Visualizar Detalhes",
                reverse("adminview_recurso_psct", kwargs=dict(pk=obj.pk)),
            )
            if obj.fase.em_periodo_analise:
                menu_obj.add(
                    "Modificar Avaliador/Homologador",
                    reverse("redistribuir_recurso_psct", kwargs=dict(pk=obj.pk)),
                )

    @tab(name="Meus Recursos")
    def meus(self, queryset):
        return queryset.filter(usuario=self.user)

    @tab(name="Recursos não Avaliados")
    def nao_avaliados(self, queryset):
        return queryset.filter(mailbox_avaliadores__avaliador=self.user).exclude(
            pareceres_avaliadores__avaliador=self.user
        )

    @tab(name="Recursos em Avaliação")
    def em_avaliacao(self, queryset):
        return queryset.filter(
            pareceres_avaliadores__avaliador=self.user,
            pareceres_avaliadores__concluido=False,
        ).distinct()

    @tab(name="Recursos Entregues")
    def entregues(self, queryset):
        return queryset.filter(
            pareceres_avaliadores__avaliador=self.user,
            pareceres_avaliadores__concluido=True,
        ).distinct()

    @tab(name="Recursos Aguardando Avaliação")
    def aguardando_avaliacao(self, queryset):
        qs = queryset.annotate(
            avaliacoes=dj_models.Sum(
                dj_models.Case(
                    dj_models.When(pareceres_avaliadores__concluido=True, then=1),
                    default=0,
                    output_field=dj_models.IntegerField(),
                )
            )
        )
        return (
            qs.filter(mailbox_homologadores__homologador=self.user)
            .exclude(avaliacoes=dj_models.F("fase__quantidade_avaliadores"))
            .distinct()
        )

    @tab(name="Recursos Aguardando Homologação")
    def aguardando_homologacao(self, queryset):
        qs = queryset.annotate(
            avaliacoes=dj_models.Sum(
                dj_models.Case(
                    dj_models.When(pareceres_avaliadores__concluido=True, then=1),
                    default=0,
                    output_field=dj_models.IntegerField(),
                )
            )
        )
        return qs.filter(
            mailbox_homologadores__homologador=self.user,
            pareceres_homologadores__isnull=True,
            avaliacoes=dj_models.F("fase__quantidade_avaliadores"),
        ).distinct()

    @tab(name="Recursos Homologados")
    def homologados(self, queryset):
        return queryset.filter(
            pareceres_homologadores__homologador=self.user
        ).distinct()

    @tab(name="Todos Recursos")
    def todos(self, queryset):
        return queryset

    def get_button_area(self):
        menu = self.get_menu_class()("Novo Recurso", button_css="success")
        for fase in models.FaseRecurso.objects.filter(
            edital__inscricao__candidato__user=self.user
        ).distinct():
            has_recurso = (
                models.Recurso.objects.filter(
                    fase=fase, inscricao__candidato__user=self.user
                )
                .distinct()
                .exists()
            )
            if fase.em_periodo_submissao and not has_recurso:
                menu.add(
                    fase, reverse("add_recurso_psct", kwargs=dict(fase_pk=fase.pk))
                )
        if self.profile.is_administrador:
            menu2 = self.get_menu_class()("Distribuir Recursos", button_css="primary")
            now = datetime.now()
            for fase in models.FaseRecurso.objects.filter():
                if fase.pode_distribuir:
                    menu2.add(
                        fase,
                        reverse("agrupar_recurso_psct", kwargs=dict(fase_pk=fase.pk)),
                    )

            if not menu2.empty:
                menu2.add_separator()

            menu2.add_header("Redistribuir Recursos de Avaliador")
            for fase in models.FaseRecurso.objects.filter():
                if fase.pode_redistribuir:
                    menu2.add(
                        fase,
                        reverse(
                            "redistribuir_avaliador_psct", kwargs=dict(fase_pk=fase.pk)
                        ),
                    )
            menu2.add_separator()
            menu2.add_header("Redistribuir Recursos de Homologador")
            for fase in models.FaseRecurso.objects.filter():
                if fase.pode_redistribuir:
                    menu2.add(
                        fase,
                        reverse(
                            "redistribuir_homologador_psct",
                            kwargs=dict(fase_pk=fase.pk),
                        ),
                    )

            return [menu, menu2]

        return [menu]

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        bc = BreadCrumb()
        data["breadcrumb"] = bc
        if utils.apenas_candidato(self.user):
            bc.add("Minhas Inscrições", reverse("index_psct"))
        bc.add("Recursos", "")
        return data

    def get_simple_filters(self):
        if self.profile.is_administrador:
            fs = (
                filters.SituacaoRecursoFilter,
                filters.AvaliadorFilter,
                filters.HomologadorFilter,
            )
            return fs + super().get_simple_filters()
        return super().get_simple_filters()

    def get_field_filters(self):
        if utils.apenas_candidato(self.user):
            return tuple()
        if self.profile.is_administrador:
            return ("fase", "inscricao__curso__campus")
        return super().get_field_filters()

    def get_list_display(self):
        if utils.apenas_candidato(self.user):
            return "curso", "fase", "situacao", "acoes"
        if self.profile.is_administrador:
            return "id", "candidato", "situacao_admin", "acoes"
        return super().get_list_display()

    def get_tabs(self):
        all_tabs = list(super().get_tabs())

        if self.profile.is_administrador:
            return all_tabs

        if utils.apenas_candidato(self.user):
            return ["meus"]

        if not models.Recurso.objects.filter(usuario=self.user).exists():
            all_tabs.remove("meus")

        if self.profile.is_avaliador:
            if not self.get_tab_queryset("nao_avaliados").exists():
                all_tabs.remove("nao_avaliados")

            if not self.get_tab_queryset("em_avaliacao").exists():
                all_tabs.remove("em_avaliacao")

            if not self.get_tab_queryset("entregues").exists():
                all_tabs.remove("entregues")
        else:
            for tab in ["nao_avaliados", "em_avaliacao", "entregues"]:
                all_tabs.remove(tab)

        if self.profile.is_homologador:
            if not self.get_tab_queryset("aguardando_avaliacao").exists():
                all_tabs.remove("aguardando_avaliacao")

            if not self.get_tab_queryset("aguardando_homologacao").exists():
                all_tabs.remove("aguardando_homologacao")

            if not self.get_tab_queryset("homologados").exists():
                all_tabs.remove("homologados")
        else:
            for tab in [
                "aguardando_avaliacao",
                "aguardando_homologacao",
                "homologados",
            ]:
                all_tabs.remove(tab)

        if not (self.profile.is_administrador or self.user.is_superuser):
            all_tabs.remove("todos")

        return all_tabs

    def get_queryset(self):
        if not self.get_tabs():
            return models.Recurso.objects.none()
        return super().get_queryset().order_by("-id")

    def get_autocomplete_fields(self):
        if utils.apenas_candidato(self.user):
            return []
        return super().get_autocomplete_fields()


class ParecerAvaliadorView(GroupRequiredMixin, generic.DetailView):
    group_required = "Avaliador PSCT"
    raise_exception = True
    model = models.ParecerAvaliador
    template_name = "psct/recurso/parecer_avaliador_detail.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.object = self.get_object()
            return self.object.avaliador == self.request.user
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        aid = self.object.id
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")), (f"Parecer #{aid}", "")
        )
        return data


class ParecerHomologadorView(GroupRequiredMixin, generic.DetailView):
    group_required = "Homologador PSCT"
    raise_exception = True
    model = models.ParecerHomologador
    template_name = "psct/recurso/parecer_homologador_detail.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.object = self.get_object()
            return self.object.homologador == self.request.user
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        aid = self.object.id
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")), (f"Parecer #{aid}", "")
        )
        return data


class ParecerView(GroupRequiredMixin, generic.DetailView):
    group_required = "Candidatos PSCT"
    raise_exception = True
    model = models.ParecerHomologador
    template_name = "psct/recurso/parecer_detail.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.object = self.get_object()
            return self.object.recurso.usuario == self.request.user
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        aid = self.object.id
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")), (f"Parecer #{aid}", "")
        )
        return data


class ListGrupoView(GroupRequiredMixin, ListView):
    group_required = "Administradores PSCT"
    raise_exception = True
    model = models.GrupoEdital
    list_display = "grupo", "edital", "acoes"
    search_fields = ("grupo__name",)
    field_filters = ("edital",)
    simple_filters = [filters.ServidorFilter]
    tabs = ["todos"]

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Grupos"
        return data

    def get_breadcrumb(self):
        return (("Grupos", ""),)

    @menu("Opções", col="Ações")
    def acoes(self, menu_obj: ListView.menu_class, obj: models.GrupoEdital) -> None:
        menu_obj.add(
            "Editar",
            reverse("change_grupo_recurso_psct", kwargs=dict(grupoedital_pk=obj.pk)),
        )

    def get_button_area(self):
        menu = self.get_menu_class()("Novo Grupo", button_css="success")
        for edital in Edital.objects.filter(processo_inscricao__isnull=False):
            label = f"Edital {edital.numero}/{edital.ano}"
            menu.add(
                label,
                reverse("add_grupo_recurso_psct", kwargs=dict(edital_pk=edital.pk)),
            )
        return [menu]

    @tab("Todos")
    def todos(self, queryset):
        return queryset


class RedistribuirRecursoView(GroupRequiredMixin, generic.DetailView):
    template_name = "psct/recurso/redistribuir.html"
    group_required = "Administradores PSCT"
    raise_exception = True
    model = models.Recurso

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")), ("Redistribuir", "")
        )
        matriculas = [
            mb.avaliador.username for mb in self.object.mailbox_avaliadores.all()
        ]
        matriculas.extend(
            [mb.homologador.username for mb in self.object.mailbox_homologadores.all()]
        )
        if matriculas:
            client = Client()
            response = client.get_servidores(matriculas)
            suapdata = {}
            for item in response:
                suapdata[item["matricula"]] = item
            data["suap"] = suapdata
        return data


class SubstituirAvaliadorView(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/recurso/substituir_avaliador.html"
    form_class = forms.SubstituirForm

    def dispatch(self, request, *args, **kwargs):
        self.avaliador = get_object_or_404(models.User, pk=self.kwargs["avaliador_pk"])
        self.recurso = get_object_or_404(models.Recurso, pk=self.kwargs["recurso_pk"])
        self.grupo = get_object_or_404(models.Group, pk=self.kwargs["grupo_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data["titulo"] = f"Substituição de {self.avaliador.get_full_name()}"
        data["recurso"] = self.recurso
        data["grupo"] = self.grupo
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")),
            (
                "Redistribuir Recurso",
                reverse(
                    "redistribuir_recurso_psct",
                    kwargs=dict(pk=self.kwargs["recurso_pk"]),
                ),
            ),
            ("Substituir Avaliador", ""),
        )
        data["nome_botao"] = "Substituir"
        client = Client()
        data["membros"] = sorted(
            client.get_servidores([u.username for u in self.grupo.user_set.all()]),
            key=lambda x: x["nome"],
        )
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["grupo"] = self.grupo
        kwargs["servidor_atual"] = self.avaliador
        kwargs["grupo_permissao"] = permissions.AvaliadorPSCT
        return kwargs

    def get_success_url(self):
        messages.info(self.request, "Avaliador substituído com sucesso")
        return reverse(
            "redistribuir_recurso_psct", kwargs=dict(pk=self.kwargs["recurso_pk"])
        )

    def form_valid(self, form):
        with transaction.atomic():
            mb = self.avaliador.mailbox_avaliador.get(fase=self.recurso.fase)
            mb.recursos.remove(self.recurso)
            novo_avaliador = form.get_user_servidor()
            mb, created = novo_avaliador.mailbox_avaliador.get_or_create(
                fase=self.recurso.fase, avaliador=novo_avaliador
            )
            mb.recursos.add(self.recurso)
        return super().form_valid(form)


class SubstituirHomologadorView(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/recurso/substituir_homologador.html"
    form_class = forms.SubstituirForm

    def dispatch(self, request, *args, **kwargs):
        self.homologador = get_object_or_404(
            models.User, pk=self.kwargs["homologador_pk"]
        )
        self.recurso = get_object_or_404(models.Recurso, pk=self.kwargs["recurso_pk"])
        self.grupo = get_object_or_404(models.Group, pk=self.kwargs["grupo_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data["titulo"] = f"Substituição de {self.homologador.get_full_name()}"
        data["recurso"] = self.recurso
        data["grupo"] = self.grupo
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")),
            (
                "Redistribuir Recurso",
                reverse(
                    "redistribuir_recurso_psct",
                    kwargs=dict(pk=self.kwargs["recurso_pk"]),
                ),
            ),
            ("Substituir Homologador", ""),
        )
        data["nome_botao"] = "Substituir"
        client = Client()
        data["membros"] = sorted(
            client.get_servidores([u.username for u in self.grupo.user_set.all()]),
            key=lambda x: x["nome"],
        )
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["grupo"] = self.grupo
        kwargs["servidor_atual"] = self.homologador
        kwargs["grupo_permissao"] = models.Group.objects.get(name="Homologador PSCT")
        return kwargs

    def get_success_url(self):
        messages.info(self.request, "Homologador substituído com sucesso")
        return reverse(
            "redistribuir_recurso_psct", kwargs=dict(pk=self.kwargs["recurso_pk"])
        )

    def form_valid(self, form):
        with transaction.atomic():
            mb = self.homologador.mailbox_homologador.get(fase=self.recurso.fase)
            mb.recursos.remove(self.recurso)
            novo_homologador = form.get_user_servidor()
            mb, created = novo_homologador.mailbox_homologador.get_or_create(
                fase=self.recurso.fase, homologador=novo_homologador
            )
            mb.recursos.add(self.recurso)
        return super().form_valid(form)


class ListGrupoPermissaoView(GroupRequiredMixin, ListView):
    group_required = "Administradores PSCT"
    raise_exception = True
    model = models.User
    tabs = ["todos"]
    list_display = ("nome", "matricula", "campus", "acoes")
    search_fields = ("username", "first_name", "last_name")
    group_name = None
    title_group = None
    url_importar = None
    ordering = ("-id",)

    @tab("Todos")
    def todos(self, queryset):
        users = queryset.filter(groups__name=self.group_name)
        if users.exists():
            self.client = Client()
            response = self.client.get_servidores([u.username for u in users])
            self.data = {}
            for userdata in response:
                self.data[userdata["matricula"]] = userdata
        else:
            self.data = {}

        return users

    @column("Nome")
    def nome(self, obj):
        if obj.username in self.data:
            return self.data[obj.username]["nome"]
        return obj.get_full_name()

    @column("Matrícula")
    def matricula(self, obj):
        if obj.username in self.data:
            return self.data[obj.username]["matricula"]
        return obj.username

    @mark_safe
    @column("Campus")
    def campus(self, obj):
        if obj.username in self.data:
            return self.data[obj.username]["campus"]
        return (
            '<span class="status status-error"><b>Servidor excluído no SUAP</b></span>'
        )

    @menu("Opções", col="Ações")
    def acoes(self, menu_obj, obj):
        group = models.Group.objects.get(name=self.group_name)
        menu_obj.add(
            "Remover do Grupo",
            reverse(
                "remover_membro_psct", kwargs=dict(usuario_pk=obj.pk, grupo_pk=group.pk)
            ),
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = self.title_group
        data["breadcrumb"] = BreadCrumb.create((self.group_name, ""))
        return data

    def get_breadcrumb(self):
        return ((self.group_name, ""),)

    def get_button_area(self):
        menu = self.get_menu_class()("Ações", button_css="primary")
        group = models.Group.objects.get(name=self.group_name)
        menu.add(
            "Editar", reverse("change_permission_group_psct", kwargs=dict(pk=group.id))
        )
        if self.url_importar:
            menu.add("Importar", reverse(self.url_importar))
        return [menu]


class ListAvaliadorView(ListGrupoPermissaoView):
    group_name = "Avaliador PSCT"
    title_group = "Avaliadores"
    field_filters = ("mailbox_avaliador__fase__edital", "mailbox_avaliador__fase")
    url_importar = "importar_avaliadores_psct"


class ListHomologadorView(ListGrupoPermissaoView):
    group_name = "Homologador PSCT"
    title_group = "Homologadores"
    field_filters = ("mailbox_homologador__fase__edital", "mailbox_homologador__fase")
    url_importar = "importar_homologadores_psct"


class UpdatePermissionGroupView(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    model = models.User
    template_name = "psct/base/display_form.html"
    form_class = forms.PermissionGroupForm
    grupos_gerenciados_urls = {
        "Avaliador PSCT": "list_avaliador_psct",
        "Homologador PSCT": "list_homologador_psct",
        "Validador de Comprovantes PSCT": "list_validador_psct",
        "CCA PSCT": "list_ccas_psct",
    }

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(
            models.Group,
            pk=self.kwargs["pk"],
            name__in=self.grupos_gerenciados_urls.keys(),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = f'Editar Membros do Grupo "{self.group.name}"'
        data["nome_botao"] = "Salvar"
        data["breadcrumb"] = BreadCrumb.create(
            (self.group.name, self.get_url()), (data["titulo"], "")
        )
        return data

    def get_success_url(self):
        messages.info(self.request, "Grupo atualizado com sucesso")
        return self.get_url()

    def get_url(self):
        return reverse(self.grupos_gerenciados_urls[self.group.name])

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = {
            "servidores": [u.username for u in self.group.user_set.all()]
        }
        kwargs["group"] = self.group
        return kwargs


class RemoverMembroView(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/recurso/remover_membro.html"
    form_class = forms.forms.Form

    def dispatch(self, request, *args, **kwargs):
        self.group = get_object_or_404(
            models.Group,
            pk=self.kwargs["grupo_pk"],
            name__in=["Avaliador PSCT", "Homologador PSCT"],
        )
        self.usuario = get_object_or_404(models.User, pk=self.kwargs["usuario_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = 'Deseja realmente remover "{}" do Grupo "{}"'.format(
            self.usuario.get_full_name(), self.group.name
        )
        data["nome_botao"] = "Remover"
        data["breadcrumb"] = BreadCrumb.create(
            (self.group.name, self.get_url()), ("Remover Membro do Grupo", "")
        )
        data["back_url"] = self.get_url()
        return data

    def get_url(self):
        if self.group.name == "Avaliador PSCT":
            return reverse("list_avaliador_psct")
        else:
            return reverse("list_homologador_psct")

    def form_valid(self, form):
        self.group.user_set.remove(self.usuario)
        return super().form_valid(form)

    def get_success_url(self):
        messages.info(self.request, "Usuário removido com sucesso")
        return self.get_url()


class RedistribuirVariosRecursosView(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/base/display_form.html"
    redistribuidor_class = None
    form_class = forms.RedistribuirForm
    group_name = None

    def dispatch(self, request, *args, **kwargs):
        self.fase = get_object_or_404(models.FaseRecurso, pk=self.kwargs["fase_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Redistribuir Recursos"
        data["nome_botao"] = "Redistribuir"
        data["breadcrumb"] = BreadCrumb.create(
            ("Recursos", reverse("list_recurso_psct")), ("Redistribuir Recurso", "")
        )
        return data

    def form_valid(self, form):
        quantidade = form.redistribuir(self.redistribuidor_class, self.group_name)
        messages.info(
            self.request, f"{quantidade} recursos foram redistribuídos com sucesso",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("list_recurso_psct")

    def get_url(self):
        raise NotImplemented

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["fase"] = self.fase
        return kwargs


class RedistribuirRecursoAvaliacaoView(RedistribuirVariosRecursosView):
    redistribuidor_class = RedistribuirRecursoAvaliador
    group_name = "Avaliador PSCT"

    def get_url(self):
        return reverse(
            "redistribuir_avaliador_psct", kwargs=dict(fase_pk=self.kwargs["fase_pk"])
        )


class RedistribuirRecursoHomologadorView(RedistribuirVariosRecursosView):
    redistribuidor_class = RedistribuirRecursoHomologador
    group_name = "Homologador PSCT"

    def get_url(self):
        return reverse(
            "redistribuir_homologador_psct", kwargs=dict(fase_pk=self.kwargs["fase_pk"])
        )


class ImportarUsuarios(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    group_url = None
    group_name = None
    form_class = forms.ImportarGrupoForm
    template_name = "psct/base/display_form.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Importar membros"
        data["nome_botao"] = "Importar"
        data["breadcrumb"] = BreadCrumb.create(
            (self.group_name, self.group_url), ("Importar membros", "")
        )
        return data

    def form_valid(self, form):
        grupo_edital = form.cleaned_data["grupo_edital"]
        grupo = models.Group.objects.get(name=self.group_name)
        grupo.user_set.add(*grupo_edital.grupo.user_set.all())
        return super().form_valid(form)

    def get_success_url(self):
        messages.info(self.request, "Membros importados com sucesso")
        return self.get_url()

    def get_url(self):
        return reverse(self.group_url)


class ImportarAvaliadores(ImportarUsuarios):
    group_name = "Avaliador PSCT"
    group_url = "list_avaliador_psct"


class ImportarHomologadores(ImportarUsuarios):
    group_name = "Homologador PSCT"
    group_url = "list_homologador_psct"


class ResultadoRecursosPdf(GroupRequiredMixin, generic.View):
    group_required = "Administradores PSCT"
    raise_exception = True

    def get(self, request, pk):
        if models.Recurso.objects.filter(pareceres_homologadores__isnull=True):
            messages.warning(
                request,
                "Há recursos que ainda não foram homologados. "
                "Por favor, efetue a homologação destes recursos antes de continuar com esta operação.",
            )
        else:
            generate_resultado_recursos_pdf.delay(request.user.id, pk)
            messages.info(
                request,
                "Seu trabalho está sendo processado e em breve você receberá um e-mail com o arquivo.",
            )
        return redirect("admin:psct_faserecurso_change", pk)
