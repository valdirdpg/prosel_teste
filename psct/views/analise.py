from datetime import datetime

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views import generic
from reversion.views import RevisionMixin

from base.custom.autocomplete import auto_complete as ac
from base.custom.datatypes import BreadCrumb
from base.custom.views import ListView
from base.custom.views.decorators import column, menu, tab
from base.custom.views.mixin import AnyGroupRequiredMixin, GroupRequiredMixin
from monitoring.models import Job
from psct.distribuicao import analise as distribuicao
from psct.filters.analise import FormacaoFilter
from psct.filters.recurso import AvaliadorFilter, EditalPSCTFilter, HomologadorFilter
from psct.forms import analise as analise_forms
from psct.forms.recurso import RedistribuirForm
from psct.models import analise as models
from psct.tasks.analise import importar


class ListInscricaoView(AnyGroupRequiredMixin, ListView):
    group_required = ("Avaliador PSCT", "Homologador PSCT", "Administradores PSCT")
    raise_exception = True
    simple_filters = (
        FormacaoFilter,
        AvaliadorFilter,
        HomologadorFilter,
        EditalPSCTFilter,
    )
    field_filters = ("curso__campus", "modalidade", "situacao")
    list_display = (
        "candidato",
        "curso_display",
        "pontuacao_display",
        "campus",
        "situacao_display",
        "acoes",
    )
    paginate_by = 10
    show_numbers = True
    tabs = [
        "nao_avaliadas",
        "em_avaliacao",
        "entregues",  # avaliador
        "aguardando_homologacao",
        "homologadas",  # homologação
        "indeferidas",  # inscrições para ajuste
        "todas",  # administrador
    ]

    autocomplete_fields = [
        ac("cursos.cursoselecao", "curso", ["curso__nome"]),
        ac("psct.candidato", "candidato", ["nome", "cpf", "user__username"]),
    ]

    model = models.InscricaoPreAnalise

    profile_checker = [
        ("avaliador", "Avaliador PSCT"),
        ("homologador", "Homologador PSCT"),
        ("administrador", "Administradores PSCT"),
    ]

    @column("Curso")
    def curso_display(self, obj):
        return f"{obj.curso.formacao} em {obj.curso.curso.nome} - {obj.curso.turno}"

    @column("Pontuação")
    def pontuacao_display(self, obj):
        return obj.pontuacao

    @column("Campus")
    def campus(self, obj):
        return obj.curso.campus

    @mark_safe
    @column("Situação")
    def situacao_display(self, obj):
        msg = obj.get_situacao_display()
        if obj.situacao == models.SituacaoInscricao.INDEFERIDA.name:
            css = "indeferido"
        elif obj.situacao == models.SituacaoInscricao.DEFERIDA.name:
            css = "deferido"
        else:
            css = "pendente"
        return f'<span class="status status-{css}">{msg}</span>'

    def get_list_display(self):
        if self.profile.is_administrador:
            return super().get_list_display()
        return "candidato", "pontuacao_display", "acoes"

    def get_field_filters(self):
        if self.profile.is_administrador:
            return super().get_field_filters()
        return []

    def get_autocomplete_fields(self):
        if self.profile.is_administrador:
            return super().get_autocomplete_fields()
        return []

    def get_simple_filters(self):
        if self.profile.is_administrador:
            return super().get_simple_filters()
        return []

    @tab("Não Avaliadas")
    def nao_avaliadas(self, queryset):
        return queryset.filter(mailbox_avaliadores__avaliador=self.user).exclude(
            avaliacoes_avaliador__avaliador=self.user
        )

    @tab("Em Avaliação")
    def em_avaliacao(self, queryset):
        return queryset.filter(
            avaliacoes_avaliador__avaliador=self.user,
            avaliacoes_avaliador__concluida=models.Concluida.NAO.name,
        )

    @tab("Entregues")
    def entregues(self, queryset):
        return queryset.filter(
            avaliacoes_avaliador__avaliador=self.user,
            avaliacoes_avaliador__concluida=models.Concluida.SIM.name,
        )

    @tab("Aguardando Homologação")
    def aguardando_homologacao(self, queryset):
        return queryset.filter(mailbox_homologadores__homologador=self.user).exclude(
            avaliacoes_homologador__homologador=self.user
        )

    @tab("Homologadas")
    def homologadas(self, queryset):
        return queryset.filter(avaliacoes_homologador__homologador=self.user)

    @tab("Indeferidas")
    def indeferidas(self, queryset):
        now = datetime.now()
        return queryset.filter(
            situacao=models.SituacaoInscricao.INDEFERIDA.name,
            fase__ajuste_pontuacao__data_inicio__lte=now,
            fase__ajuste_pontuacao__data_encerramento__gte=now,
            pilhainscricaoajuste__isnull=True,
        ).distinct()

    @tab("Todas")
    def todas(self, queryset):
        return queryset

    def get_tabs(self):

        if self.profile.is_administrador:
            return super().get_tabs()

        tabs = []
        if self.profile.is_avaliador:
            tabs.extend(["nao_avaliadas", "em_avaliacao", "entregues"])
        if self.profile.is_homologador:
            tabs.extend(["aguardando_homologacao", "homologadas"])
        return tabs

    def get_queryset(self):
        tabs = self.get_tabs()
        if tabs:
            return super().get_queryset()
        return super().get_queryset().none()

    @menu("Opções", "Ações")
    def acoes(self, menu_obj, obj):
        if self.profile.is_avaliador:
            self.get_menu_avaliador(menu_obj, obj)
        if self.profile.is_homologador:
            self.get_menu_homologador(menu_obj, obj)
        if self.profile.is_administrador:
            self.get_menu_administrador(menu_obj, obj)

    def get_menu_avaliador(self, menu, obj):

        if not self.user.mailbox_avaliador_inscricao.filter(inscricoes=obj):
            return

        avaliacao = obj.avaliacoes_avaliador.filter(avaliador=self.user).first()
        if obj.fase.acontecendo:
            if not avaliacao:
                menu.add(
                    "Avaliar",
                    reverse(
                        "add_avaliacao_avaliador_inscricao_psct",
                        kwargs=dict(inscricao_pk=obj.pk),
                    ),
                )
            elif not avaliacao.is_concluida:
                menu.add(
                    "Editar avaliação",
                    reverse(
                        "change_avaliacao_avaliador_inscricao_psct",
                        kwargs=dict(pk=avaliacao.pk),
                    ),
                )
        if avaliacao and avaliacao.is_concluida:
            menu.add(
                "Visualizar avaliação",
                reverse(
                    "view_avaliacao_avaliador_inscricao_psct",
                    kwargs=dict(pk=avaliacao.pk),
                ),
            )

    def get_menu_homologador(self, menu, obj):

        if not self.user.mailbox_homologador_inscricao.filter(inscricoes=obj):
            return

        avaliacao = obj.avaliacao

        if avaliacao and avaliacao.homologador != self.user:
            return

        if obj.fase.acontecendo:
            if not avaliacao:
                menu.add(
                    "Homologar",
                    reverse(
                        "add_avaliacao_homologador_inscricao_psct",
                        kwargs=dict(inscricao_pk=obj.pk),
                    ),
                )
            else:
                menu.add(
                    "Editar avaliação",
                    reverse(
                        "change_avaliacao_homologador_inscricao_psct",
                        kwargs=dict(pk=avaliacao.pk),
                    ),
                )
        if avaliacao:
            menu.add(
                "Visualizar avaliação",
                reverse(
                    "view_avaliacao_homologador_inscricao_psct",
                    kwargs=dict(pk=avaliacao.pk),
                ),
            )

    def get_menu_administrador(self, menu, obj):
        menu.add(
            "Visualizar detalhes",
            reverse("view_avaliacao_inscricao_psct", kwargs=dict(pk=obj.pk)),
        )
        menu.add(
            "Visualizar inscrição",
            reverse("visualizar_inscricao_psct", kwargs=dict(pk=obj.inscricao.id)),
        )
        menu.add(
            "Enviar para correção",
            reverse(
                "add_pilha_pontuacao_psct",
                kwargs=dict(fase_pk=obj.fase_id, inscricao_pk=obj.id),
            ),
        )

    def get_button_area(self):
        menu_list = []
        menu_class = self.get_menu_class()
        menu_avaliador = menu_class("Obter Inscrições para Análise")
        menu_homologador = menu_class("Obter Inscrições para Homologação")
        menu_inscricoes = menu_class("Importar Inscrições")

        fases = models.FaseAnalise.objects.all()

        for fase in fases:
            if fase.acontecendo:
                if (
                    self.profile.is_avaliador
                    and not models.MailBoxAvaliadorInscricao.possui_inscricao_pendente(
                        fase, self.user
                    )
                ):

                    if fase.eh_avaliador(
                        self.user
                    ) and models.ProgressoAnalise.existe_avaliacao_pendente(fase):
                        menu_avaliador.add_header(fase)

                        def get_url(qnt):
                            return reverse(
                                "add_lote_avaliador_inscricao_psct",
                                kwargs=dict(fase_pk=fase.id, quantidade=qnt),
                            )

                        menu_avaliador.add_many(
                            ("05 - Inscrições", get_url(5)),
                            ("10 - Inscrições", get_url(10)),
                            ("20 - Inscrições", get_url(20)),
                        )
                if (
                    self.profile.is_homologador
                    and not models.MailBoxHomologadorInscricao.possui_inscricao_pendente(
                        fase, self.user
                    )
                ):

                    if fase.eh_homologador(self.user):
                        menu_homologador.add_header(fase)

                        def get_url(qnt):
                            return reverse(
                                "add_lote_homologador_inscricao_psct",
                                kwargs=dict(fase_pk=fase.id, quantidade=qnt),
                            )

                        menu_homologador.add_many(
                            ("05 - Inscrições", get_url(5)),
                            ("10 - Inscrições", get_url(10)),
                            ("20 - Inscrições", get_url(20)),
                        )

                if (
                    self.profile.is_administrador
                    and not models.InscricaoPreAnalise.objects.filter(
                        fase=fase
                    ).exists()
                ):
                    menu_inscricoes.add(
                        fase,
                        reverse(
                            "analise_importar_inscricao_psct",
                            kwargs=dict(fase_pk=fase.id),
                        ),
                    )

        if self.profile.is_administrador:
            menu_distribuicao = menu_class("Distribuir Inscrição", button_css="primary")

            menu_distribuicao.add_header("Definir Regras")
            for fase in fases:
                if fase.acontecendo:
                    menu_distribuicao.add(
                        fase,
                        reverse(
                            "regra_exclusao_inscricao_psct",
                            kwargs=dict(fase_pk=fase.pk),
                        ),
                    )

            if not menu_distribuicao.empty:
                menu_distribuicao.add_separator()

            menu_distribuicao.add_header("Redistribuir Inscrição de Avaliador")
            for fase in fases:
                if fase.acontecendo:
                    menu_distribuicao.add(
                        fase,
                        reverse(
                            "redistribuir_inscricao_avaliador_psct",
                            kwargs=dict(fase_pk=fase.pk),
                        ),
                    )

            menu_distribuicao.add_separator()
            menu_distribuicao.add_header("Redistribuir Inscrição de Homologador")
            for fase in fases:
                if fase.acontecendo:
                    menu_distribuicao.add(
                        fase,
                        reverse(
                            "redistribuir_inscricao_homologador_psct",
                            kwargs=dict(fase_pk=fase.pk),
                        ),
                    )

            menu_list.append(menu_distribuicao)

        if not menu_avaliador.empty:
            menu_list.append(menu_avaliador)
        if not menu_homologador.empty:
            menu_list.append(menu_homologador)
        if not menu_inscricoes.empty:
            menu_list.append(menu_inscricoes)
        return menu_list

    def get_breadcrumb(self):
        return [("Inscrições para Análise", "")]

    def get_title(self):
        return "Inscrições para Análise"


class CreateLoteAvaliadorInscricaoView(GroupRequiredMixin, generic.FormView):
    group_required = "Avaliador PSCT"
    raise_exception = True
    form_class = forms.Form
    template_name = "psct/base/confirmacao.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.fase = get_object_or_404(models.FaseAnalise, pk=self.kwargs["fase_pk"])

            if self.fase.eh_avaliador(self.request.user):
                return not models.MailBoxAvaliadorInscricao.possui_inscricao_pendente(
                    self.fase, self.request.user
                )
            return False
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Deseja obter {} inscrições para análise?".format(
            self.kwargs["quantidade"]
        )
        data["back_url"] = reverse("list_inscricao_psct")
        data["nome_botao"] = "Confirmar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")), ("Obter Inscrições", "")
        )
        return data

    def get(self, request, *args, **kwargs):
        if int(self.kwargs["quantidade"]) not in [5, 10, 20]:
            raise Http404()
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        quantidade = models.get_lote_avaliador(
            self.fase, self.request.user, int(self.kwargs["quantidade"])
        )
        messages.info(
            self.request,
            f"Foram adicionadas {quantidade} inscrições em sua caixa de avaliação",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("list_inscricao_psct") + "?tab=nao_avaliadas"


class ImportarInscricaoView(GroupRequiredMixin, generic.FormView):
    raise_exception = True
    template_name = "psct/base/confirmacao.html"
    form_class = forms.Form
    group_required = "Administradores PSCT"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        fase = get_object_or_404(models.FaseAnalise, pk=self.kwargs["fase_pk"])
        data["titulo"] = "Deseja importar inscrições do edital {} para análise?".format(
            fase.edital
        )
        data["back_url"] = reverse("list_inscricao_psct")
        data["nome_botao"] = "Confirmar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")), ("Importar Inscrições", "")
        )
        return data

    def get_success_url(self):
        return self.job.get_absolute_url()

    def form_valid(self, form):
        messages.info(self.request, "Processo de importação iniciado com sucesso")
        async_result = importar.delay(self.kwargs["fase_pk"])
        self.job = Job.new(self.request.user, async_result, name=importar.name)
        return super().form_valid(form)


class RedistribuirInscricaoView(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/base/display_form.html"
    redistribuidor_class = None
    form_class = RedistribuirForm
    group_name = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.fase = get_object_or_404(models.FaseAnalise, pk=kwargs["fase_pk"])

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Redistribuir Inscrições"
        data["nome_botao"] = "Redistribuir"
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")),
            ("Redistribuir Inscrição", ""),
        )
        return data

    def form_valid(self, form):
        quantidade = form.redistribuir(self.redistribuidor_class, self.group_name)
        messages.info(
            self.request, f"{quantidade} inscrições foram redistribuídas com sucesso",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("list_inscricao_psct")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["fase"] = self.fase
        return kwargs


class RedistribuirInscricaoAvaliacaoView(RedistribuirInscricaoView):
    redistribuidor_class = distribuicao.RedistribuirInscricaoAvaliador
    group_name = "Avaliador PSCT"


class RedistribuirInscricaoHomologadorView(RedistribuirInscricaoView):
    redistribuidor_class = distribuicao.RedistribuirInscricaoHomologador
    group_name = "Homologador PSCT"


class RegraExclusaoView(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/base/display_form.html"
    form_class = analise_forms.CriterioExclusaoForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        try:
            self.fase = models.FaseAnalise.objects.get(pk=kwargs["fase_pk"])
        except models.FaseAnalise.DoesNotExist:
            self.fase = None

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Regra de Permissão para Análise"
        data["nome_botao"] = "Selecionar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")),
            ("Regra de Permissão para Análise", ""),
        )
        return data

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            if not self.fase:
                raise Http404()
            return self.fase.acontecendo
        return perm

    def form_valid(self, form):
        self.coluna = form.cleaned_data["criterio"]
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "grupo_regra_exclusao_inscricao_psct",
            kwargs=dict(fase_pk=self.kwargs["fase_pk"], coluna_pk=self.coluna.pk),
        )


class GrupoRegraExclusaoView(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/base/display_form.html"
    form_class = analise_forms.GrupoExclusaoForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        try:
            self.fase = models.FaseAnalise.objects.get(pk=kwargs["fase_pk"])
        except models.FaseAnalise.DoesNotExist:
            self.fase = None
        try:
            self.coluna = models.Coluna.objects.get(pk=kwargs["coluna_pk"])
        except models.Coluna.DoesNotExist:
            self.coluna = None

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            if not self.fase or not self.coluna:
                raise Http404()
            return self.fase.acontecendo
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Definir Grupos de Exclusão"
        data["nome_botao"] = "Salvar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")),
            (
                "Regra de Permissão para Análise",
                reverse(
                    "regra_exclusao_inscricao_psct",
                    kwargs=dict(fase_pk=self.kwargs["fase_pk"]),
                ),
            ),
            ("Definir Grupos de Exclusão", ""),
        )
        return data

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["coluna"] = self.coluna
        kwargs["fase"] = self.fase
        return kwargs

    def get_success_url(self):
        messages.info(self.request, "Regras definidas com sucesso!")
        return reverse("list_inscricao_psct")


class CreateLoteHomologadorInscricaoView(GroupRequiredMixin, generic.FormView):
    group_required = "Homologador PSCT"
    raise_exception = True
    form_class = forms.Form
    template_name = "psct/base/confirmacao.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.fase = get_object_or_404(models.FaseAnalise, pk=self.kwargs["fase_pk"])

            if self.fase.eh_homologador(self.request.user):
                return not models.MailBoxHomologadorInscricao.possui_inscricao_pendente(
                    self.fase, self.request.user
                )
            return False
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Deseja obter {} inscrições para homologação?".format(
            self.kwargs["quantidade"]
        )
        data["back_url"] = reverse("list_inscricao_psct")
        data["nome_botao"] = "Confirmar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")), ("Obter Inscrições", "")
        )
        return data

    def get(self, request, *args, **kwargs):
        if int(self.kwargs["quantidade"]) not in [5, 10, 20]:
            raise Http404()
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        quantidade = models.get_lote_homologador(
            self.fase, self.request.user, int(self.kwargs["quantidade"])
        )
        messages.info(
            self.request,
            f"Foram adicionadas {quantidade} inscrições em sua caixa de homologação",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("list_inscricao_psct") + "?tab=aguardando_homologacao"


class CreateAvaliacaoAvaliadorInscricaoView(
    RevisionMixin, GroupRequiredMixin, generic.CreateView
):
    model = models.AvaliacaoAvaliador
    group_required = "Avaliador PSCT"
    raise_exception = True
    form_class = analise_forms.AvaliarInscricaoAvaliadorForm
    template_name = "psct/analise/avaliacaoavaliador.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        try:
            self.inscricao_pre_analise = models.InscricaoPreAnalise.objects.get(
                pk=kwargs["inscricao_pk"]
            )
        except models.InscricaoPreAnalise.DoesNotExist:
            self.inscricao_pre_analise = None

        if self.inscricao_pre_analise:
            self.inscricao_original = self.inscricao_pre_analise.inscricao

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            if not self.inscricao_pre_analise:
                raise PermissionDenied

            if (
                self.inscricao_pre_analise.avaliacoes_avaliador.count()
                > self.inscricao_pre_analise.fase.quantidade_avaliadores
            ):
                return False

            return (
                self.inscricao_pre_analise.mailbox_avaliadores.filter(
                    avaliador=self.request.user
                ).exists()
                and not self.inscricao_pre_analise.avaliacoes_avaliador.filter(
                    avaliador=self.request.user
                ).exists()
                and self.inscricao_pre_analise.fase.acontecendo
            )

        return perm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["inscricao"] = self.inscricao_pre_analise
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = f"Avaliação da {self.inscricao_original}"
        data["nome_botao"] = "Salvar"
        data["inscricao"] = self.inscricao_pre_analise
        data["inscricao_original"] = self.inscricao_original
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")), ("Avaliar inscrição", "")
        )
        return data

    def get_initial(self):
        return {"inscricao": self.inscricao_pre_analise, "avaliador": self.request.user}

    def get_success_url(self):
        messages.info(self.request, "Avaliação salva com sucesso")
        return reverse("list_inscricao_psct") + "?tab=nao_avaliadas"

    def form_invalid(self, form):
        messages.error(
            self.request, "Por favor, corrija os erros abaixo para continuar."
        )
        return super().form_invalid(form)


class UpdateAvaliacaoAvaliadorInscricaoView(
    RevisionMixin, GroupRequiredMixin, generic.UpdateView
):
    model = models.AvaliacaoAvaliador
    group_required = "Avaliador PSCT"
    raise_exception = True
    form_class = analise_forms.AvaliarInscricaoAvaliadorForm
    template_name = "psct/analise/avaliacaoavaliador.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        try:
            self.avaliacao = models.AvaliacaoAvaliador.objects.get(pk=kwargs["pk"])
        except models.AvaliacaoAvaliador.DoesNotExist:
            self.avaliacao = None

        if self.avaliacao:
            self.inscricao_pre_analise = self.avaliacao.inscricao
            self.inscricao_original = self.inscricao_pre_analise.inscricao

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            if not self.avaliacao:
                raise PermissionDenied
            return self.avaliacao.pode_alterar(self.request.user)
        return perm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["inscricao"] = self.avaliacao.inscricao
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["nome_botao"] = "Salvar"
        data["titulo"] = f"Avaliação da {self.inscricao_original}"
        data["inscricao"] = self.inscricao_pre_analise
        data["inscricao_original"] = self.inscricao_original
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")), ("Avaliar inscrição", "")
        )
        return data

    def get_success_url(self):
        messages.info(self.request, "Avaliação salva com sucesso")
        return reverse("list_inscricao_psct") + "?tab=nao_avaliadas"

    def form_invalid(self, form):
        messages.error(
            self.request, "Por favor, corrija os erros abaixo para continuar."
        )
        return super().form_invalid(form)


class AvaliacaoAvaliadorView(GroupRequiredMixin, generic.DetailView):
    model = models.AvaliacaoAvaliador
    group_required = "Avaliador PSCT"
    raise_exception = True
    template_name = "psct/analise/avaliacaoavaliador_detail.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        try:
            self.avaliacao = models.AvaliacaoAvaliador.objects.get(pk=kwargs["pk"])
        except models.AvaliacaoAvaliador.DoesNotExist:
            self.avaliacao = None

        if self.avaliacao:
            self.inscricao_pre_analise = self.avaliacao.inscricao
            self.inscricao_original = self.inscricao_pre_analise.inscricao

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            if not self.avaliacao:
                raise PermissionDenied
            return self.avaliacao.is_owner(self.request.user)
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data["titulo"] = f"Avaliação da {self.inscricao_original}"
        data["inscricao"] = self.inscricao_pre_analise
        data["inscricao_original"] = self.inscricao_original
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")),
            (f"Avaliação #{self.avaliacao.id}", ""),
        )
        return data


class CreateAvaliacaoHomologadorInscricaoView(
    RevisionMixin, GroupRequiredMixin, generic.CreateView
):
    model = models.AvaliacaoHomologador
    group_required = "Homologador PSCT"
    raise_exception = True
    form_class = analise_forms.AvaliarInscricaoHomologadorForm
    template_name = "psct/analise/avaliacaohomologador.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        try:
            self.inscricao_pre_analise = models.InscricaoPreAnalise.objects.get(
                pk=kwargs["inscricao_pk"]
            )
        except models.InscricaoPreAnalise.DoesNotExist:
            self.inscricao_pre_analise = None

        if self.inscricao_pre_analise:
            self.inscricao_original = self.inscricao_pre_analise.inscricao

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            if not self.inscricao_pre_analise:
                raise PermissionDenied
            return (
                self.inscricao_pre_analise.mailbox_homologadores.filter(
                    homologador=self.request.user
                ).exists()
                and not self.inscricao_pre_analise.avaliacoes_homologador.exists()
                and self.inscricao_pre_analise.fase.acontecendo
            )

        return perm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["inscricao"] = self.inscricao_pre_analise
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = f"Avaliação da {self.inscricao_original}"
        data["nome_botao"] = "Salvar"
        data["inscricao"] = self.inscricao_pre_analise
        data["inscricao_original"] = self.inscricao_original
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")), ("Avaliar inscrição", "")
        )
        return data

    def get_initial(self):
        return {
            "inscricao": self.inscricao_pre_analise,
            "homologador": self.request.user,
        }

    def get_success_url(self):
        messages.info(self.request, "Avaliação salva com sucesso")
        return reverse("list_inscricao_psct") + "?tab=homologadas"

    def form_invalid(self, form):
        messages.error(
            self.request, "Por favor, corrija os erros abaixo para continuar."
        )
        return super().form_invalid(form)


class UpdateAvaliacaoHomologadorInscricaoView(
    RevisionMixin, GroupRequiredMixin, generic.UpdateView
):
    model = models.AvaliacaoHomologador
    group_required = "Homologador PSCT"
    raise_exception = True
    form_class = analise_forms.AvaliarInscricaoHomologadorForm
    template_name = "psct/analise/avaliacaohomologador.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        try:
            self.avaliacao = models.AvaliacaoHomologador.objects.get(pk=kwargs["pk"])
        except models.AvaliacaoHomologador.DoesNotExist:
            self.avaliacao = None

        if self.avaliacao:
            self.inscricao_pre_analise = self.avaliacao.inscricao
            self.inscricao_original = self.inscricao_pre_analise.inscricao

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            if not self.avaliacao:
                raise PermissionDenied
            return self.avaliacao.pode_alterar(self.request.user)
        return perm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["inscricao"] = self.avaliacao.inscricao
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["nome_botao"] = "Salvar"
        data["titulo"] = f"Avaliação da {self.inscricao_original}"
        data["inscricao"] = self.inscricao_pre_analise
        data["inscricao_original"] = self.inscricao_original
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")), ("Avaliar inscrição", "")
        )
        return data

    def get_success_url(self):
        messages.info(self.request, "Avaliação salva com sucesso")
        return reverse("list_inscricao_psct") + "?tab=homologadas"

    def form_invalid(self, form):
        messages.error(
            self.request, "Por favor, corrija os erros abaixo para continuar."
        )
        return super().form_invalid(form)


class AvaliacaoHomologadorView(GroupRequiredMixin, generic.DetailView):
    model = models.AvaliacaoHomologador
    group_required = "Homologador PSCT"
    raise_exception = True
    template_name = "psct/analise/avaliacaohomologador_detail.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        try:
            self.avaliacao = models.AvaliacaoHomologador.objects.get(pk=kwargs["pk"])
        except models.AvaliacaoHomologador.DoesNotExist:
            self.avaliacao = None

        if self.avaliacao:
            self.inscricao_pre_analise = self.avaliacao.inscricao
            self.inscricao_original = self.inscricao_pre_analise.inscricao

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            if not self.avaliacao:
                raise PermissionDenied
            return self.avaliacao.is_owner(self.request.user)
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data["titulo"] = f"Avaliação da {self.inscricao_original}"
        data["inscricao"] = self.inscricao_pre_analise
        data["inscricao_original"] = self.inscricao_original
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")),
            (f"Avaliação #{self.avaliacao.id}", ""),
        )
        return data


class AvaliacaoAdminView(GroupRequiredMixin, generic.DetailView):
    model = models.InscricaoPreAnalise
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/analise/avaliacao_detail.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.inscricao_pre_analise = get_object_or_404(
                models.InscricaoPreAnalise, pk=self.kwargs["pk"]
            )
            self.inscricao_original = self.inscricao_pre_analise.inscricao
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data["titulo"] = f"Avaliação da {self.inscricao_original}"
        data["inscricao"] = self.inscricao_pre_analise
        data["inscricao_original"] = self.inscricao_original
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")), ("Avaliação", "")
        )
        return data
