import extra_views
from django import forms
from django.contrib import messages
from django.db.models import Q
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
from base.shortcuts import get_object_or_permission_denied
from psct.distribuicao import pontuacao as distribuicao
from psct.filters import analise as analise_filters
from psct.filters import pontuacao as pontuacao_filters
from psct.forms import pontuacao as pontuacao_forms
from psct.forms.recurso import RedistribuirForm
from psct.models import analise as analise_models
from psct.models import pontuacao as models


class AddInscricaoPilhaView(GroupRequiredMixin, generic.FormView):
    raise_exception = True
    group_required = "Administradores PSCT"
    form_class = forms.Form
    template_name = "psct/pontuacao/empilhar.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.fase = get_object_or_404(
                analise_models.FaseAnalise, pk=self.kwargs["fase_pk"]
            )
            self.inscricao = get_object_or_404(
                analise_models.InscricaoPreAnalise, pk=self.kwargs["inscricao_pk"]
            )
            try:
                self.pilha, created = models.PilhaInscricaoAjuste.objects.get_or_create(
                    fase=self.fase.ajuste_pontuacao
                )
                return True
            except models.FaseAjustePontuacao.DoesNotExist:
                return False
        return False

    def form_valid(self, form):
        self.pilha.inscricoes.add(self.inscricao)
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Inscrição enviada para correção com sucesso.")
        return reverse("list_inscricao_psct") + "?tab=indeferidas"

    def get_context_data(self, **kwargs):
        data = super().get_context_data()
        data["titulo"] = "Enviar inscrição para correção"
        data["back_url"] = reverse("list_inscricao_psct") + "?tab=indeferidas"
        data["nome_botao"] = "Sim"
        data["inscricao"] = self.inscricao

        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_inscricao_psct")),
            ("Enviar inscrição para correção", ""),
        )

        return data


class ListInscricaoPontuacaoView(AnyGroupRequiredMixin, ListView):
    group_required = ("Avaliador PSCT", "Homologador PSCT", "Administradores PSCT")
    raise_exception = True
    simple_filters = (
        analise_filters.FormacaoFilter,
        pontuacao_filters.AvaliadorFilter,
        pontuacao_filters.HomologadorFilter,
        pontuacao_filters.FaseAjustePontuacaoFilter,
        pontuacao_filters.IndeferimentoEspecialFilter,
    )
    field_filters = ("curso__campus", "modalidade", "situacao", "fase")
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
        "aguardando_ajuste",
        "nao_concluidas",
        "entregues",  # avaliador
        "aguardando_homologacao",
        "homologadas",  # homologação
        "todas",  # administrador
    ]

    autocomplete_fields = [
        ac("cursos.cursoselecao", "curso", ["curso__nome"]),
        ac("psct.candidato", "candidato", ["nome", "cpf", "user__username"]),
    ]

    model = analise_models.InscricaoPreAnalise

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
        if obj.situacao == analise_models.SituacaoInscricao.INDEFERIDA.name:
            css = "indeferido"
        elif obj.situacao == analise_models.SituacaoInscricao.DEFERIDA.name:
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

    @tab("Aguardando Ajuste")
    def aguardando_ajuste(self, queryset):
        return queryset.filter(
            mailbox_pontuacao_avaliador__avaliador=self.user
        ).exclude(pontuacoes_avaliadores__avaliador=self.user)

    @tab("Não Concluídas")
    def nao_concluidas(self, queryset):
        return queryset.filter(
            pontuacoes_avaliadores__avaliador=self.user,
            pontuacoes_avaliadores__concluida=analise_models.Concluida.NAO.name,
        )

    @tab("Entregues")
    def entregues(self, queryset):
        return queryset.filter(
            pontuacoes_avaliadores__avaliador=self.user,
            pontuacoes_avaliadores__concluida=analise_models.Concluida.SIM.name,
        )

    @tab("Aguardando Homologação")
    def aguardando_homologacao(self, queryset):
        return queryset.filter(
            mailbox_pontuacao_homologador__homologador=self.user
        ).exclude(pontuacoes_homologadores__homologador=self.user)

    @tab("Homologadas")
    def homologadas(self, queryset):
        return queryset.filter(pontuacoes_homologadores__homologador=self.user)

    @tab("Todas")
    def todas(self, queryset):
        return queryset.filter(pilhainscricaoajuste__isnull=False).distinct()

    def get_tabs(self):

        if self.profile.is_administrador:
            return super().get_tabs()

        tabs = []
        if self.profile.is_avaliador:
            tabs.extend(["aguardando_ajuste", "nao_concluidas", "entregues"])
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
        if self.profile.is_homologador or self.profile.is_administrador:
            if obj.indeferida and obj.fase.ajuste_pontuacao.acontecendo:
                indeferimento_especial = getattr(obj, "indeferimento_especial", None)
                if not indeferimento_especial:
                    menu_obj.add(
                        "Adicionar indeferimento especial",
                        reverse(
                            "add_indeferimento_especial",
                            kwargs=dict(inscricao_pk=obj.pk),
                        ),
                    )
                else:
                    menu_obj.add(
                        "Editar indeferimento especial",
                        reverse(
                            "change_indeferimento_especial",
                            kwargs=dict(pk=indeferimento_especial.pk),
                        ),
                    )
                    menu_obj.add(
                        "Remover indeferimento especial",
                        reverse(
                            "delete_indeferimento_especial",
                            kwargs=dict(pk=indeferimento_especial.pk),
                        ),
                    )

        if self.profile.is_administrador:
            self.get_menu_administrador(menu_obj, obj)

    def get_menu_avaliador(self, menu, obj):

        mb = self.user.mailbox_pontuacao_avaliador.filter(inscricoes=obj).first()

        if not mb:
            return

        if mb.pode_devolver(obj):
            menu.add(
                "Devolver",
                reverse(
                    "devolver_pontuacao_avaliador_psct",
                    kwargs=dict(mailbox_pk=mb.pk, inscricao_pk=obj.pk),
                ),
            )
            return

        pontuacao = obj.pontuacoes_avaliadores.filter(avaliador=self.user).first()
        if obj.fase.ajuste_pontuacao.acontecendo:
            if not pontuacao:
                menu.add(
                    "Ajustar pontuação",
                    reverse(
                        "add_pontuacao_avaliador_psct",
                        kwargs=dict(
                            inscricao_pk=obj.pk, fase_pk=obj.fase.ajuste_pontuacao.pk
                        ),
                    ),
                )
            elif not pontuacao.is_concluida:
                menu.add(
                    "Editar pontuação",
                    reverse(
                        "change_pontuacao_avaliador_psct", kwargs=dict(pk=pontuacao.pk)
                    ),
                )
        if pontuacao and pontuacao.is_concluida:
            menu.add(
                "Visualizar pontuação",
                reverse("view_pontuacao_avaliador_psct", kwargs=dict(pk=pontuacao.pk)),
            )

    def get_menu_homologador(self, menu, obj):

        mb = self.user.mailbox_pontuacao_homologador.filter(inscricoes=obj).first()

        if not mb:
            return

        if mb.pode_devolver(obj):
            menu.add(
                "Devolver",
                reverse(
                    "devolver_pontuacao_homologador_psct",
                    kwargs=dict(mailbox_pk=mb.pk, inscricao_pk=obj.pk),
                ),
            )
            return

        pontuacao = obj.pontuacoes_homologadores.filter(homologador=self.user).first()
        if obj.fase.ajuste_pontuacao.acontecendo:
            if not pontuacao:
                menu.add(
                    "Homologar pontuação",
                    reverse(
                        "add_pontuacao_homologador_psct",
                        kwargs=dict(
                            inscricao_pk=obj.pk, fase_pk=obj.fase.ajuste_pontuacao.pk
                        ),
                    ),
                )
            else:
                menu.add(
                    "Editar homologação de pontuação",
                    reverse(
                        "change_pontuacao_homologador_psct",
                        kwargs=dict(pk=pontuacao.pk),
                    ),
                )
        if pontuacao:
            menu.add(
                "Visualizar pontuação",
                reverse(
                    "view_pontuacao_homologador_psct", kwargs=dict(pk=pontuacao.pk)
                ),
            )

    def get_menu_administrador(self, menu, obj):
        menu.add(
            "Visualizar detalhes",
            reverse("view_pontuacao_inscricao_psct", kwargs=dict(pk=obj.pk)),
        )
        menu.add(
            "Visualizar inscrição",
            reverse("visualizar_inscricao_psct", kwargs=dict(pk=obj.inscricao.id)),
        )

    def get_button_area(self):
        menu_list = []
        menu_class = self.get_menu_class()
        menu_avaliador = menu_class("Obter Inscrições para Ajuste")
        menu_homologador = menu_class("Obter Inscrições para Homologação")

        fases = models.FaseAjustePontuacao.objects.all()

        for fase in fases:
            if fase.acontecendo:
                if (
                    self.profile.is_avaliador
                    and not models.MailboxPontuacaoAvaliador.possui_inscricao_pendente(
                        fase, self.user
                    )
                ):

                    if (
                        fase.eh_avaliador(self.user)
                        and fase.existe_inscricao_pendente_ajuste()
                    ):
                        menu_avaliador.add_header(fase)

                        def get_url(qnt):
                            return reverse(
                                "add_lote_avaliador_pontuacao_psct",
                                kwargs=dict(fase_pk=fase.id, quantidade=qnt),
                            )

                        menu_avaliador.add_many(
                            ("05 - Inscrições", get_url(5)),
                            ("10 - Inscrições", get_url(10)),
                            ("20 - Inscrições", get_url(20)),
                        )

                if (
                    self.profile.is_homologador
                    and not models.MailboxPontuacaoHomologador.possui_inscricao_pendente(
                        fase, self.user
                    )
                ):

                    if (
                        fase.eh_homologador(self.user)
                        and fase.existe_inscricao_pendente_homologacao()
                    ):
                        menu_homologador.add_header(fase)

                        def get_url(qnt):
                            return reverse(
                                "add_lote_homologador_pontuacao_psct",
                                kwargs=dict(fase_pk=fase.id, quantidade=qnt),
                            )

                        menu_homologador.add_many(
                            ("05 - Inscrições", get_url(5)),
                            ("10 - Inscrições", get_url(10)),
                            ("20 - Inscrições", get_url(20)),
                        )

        if self.profile.is_administrador:
            menu_distribuicao = menu_class(
                "Redistribuir Inscrição", button_css="primary"
            )

            if not menu_distribuicao.empty:
                menu_distribuicao.add_separator()

            menu_distribuicao.add_header("Redistribuir Inscrição de Avaliador")
            for fase in fases:
                if fase.acontecendo:
                    menu_distribuicao.add(
                        fase,
                        reverse(
                            "redistribuir_pontuacao_avaliador_psct",
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
                            "redistribuir_pontuacao_homologador_psct",
                            kwargs=dict(fase_pk=fase.pk),
                        ),
                    )

            menu_list.append(menu_distribuicao)

            menu_importacao = menu_class("Importar Inscrições", button_css="primary")
            for fase in models.FaseAjustePontuacao.objects.all():
                if fase.acontecendo:
                    menu_importacao.add(
                        fase,
                        reverse(
                            "importar_inscricao_pontuacao_psct",
                            kwargs=dict(fase_pk=fase.fase_analise.pk),
                        ),
                    )
            if not menu_importacao.empty:
                menu_list.append(menu_importacao)

        if not menu_avaliador.empty:
            menu_list.append(menu_avaliador)
        if not menu_homologador.empty:
            menu_list.append(menu_homologador)
        return menu_list

    def get_breadcrumb(self):
        return [("Inscrições para Ajuste", "")]

    def get_title(self):
        return "Inscrições para Ajuste"


class CreateLoteAvaliadorPontuacaoView(GroupRequiredMixin, generic.FormView):
    group_required = "Avaliador PSCT"
    raise_exception = True
    form_class = forms.Form
    template_name = "psct/base/confirmacao.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.fase = get_object_or_404(
                models.FaseAjustePontuacao, pk=self.kwargs["fase_pk"]
            )

            if self.fase.eh_avaliador(self.request.user):
                return not models.MailboxPontuacaoAvaliador.possui_inscricao_pendente(
                    self.fase, self.request.user
                )
            return False
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Deseja obter {} inscrições para ajuste?".format(
            self.kwargs["quantidade"]
        )
        data["back_url"] = reverse("list_pontuacao_inscricao_psct")
        data["nome_botao"] = "Confirmar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_pontuacao_inscricao_psct")),
            ("Obter Inscrições", ""),
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
        return reverse("list_pontuacao_inscricao_psct") + "?tab=aguardando_ajuste"


class NotaAnualInline(extra_views.InlineFormSet):
    exclude = []
    form_class = pontuacao_forms.NotaForm
    formset_class = pontuacao_forms.NotasFormSet
    fields = ("ano", "portugues", "matematica", "historia", "geografia")
    factory_kwargs = {"max_num": 3, "extra": 3}

    def get_factory_kwargs(self):
        kwargs = super().get_factory_kwargs()
        kwargs["min_num"] = 1
        kwargs["validate_min"] = True
        kwargs["validate_max"] = True
        fields = list(kwargs["fields"])
        if not self.view.inscricao_original.is_integrado:
            fields.remove("historia")
            fields.remove("geografia")

        kwargs["fields"] = tuple(fields)
        return kwargs

    def get_initial(self):
        data = []
        if self.request.method == "GET" and not self.view.object:
            for nota in self.view.inscricao_original.pontuacao.notas.all():
                data.append(
                    {
                        "ano": nota.ano,
                        "portugues": nota.portugues,
                        "historia": nota.historia,
                        "geografia": nota.geografia,
                        "matematica": nota.matematica,
                    }
                )
        return data

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        kwargs["pontuacao"] = self.view.object
        return kwargs


class NotaAnualAvaliadorInline(NotaAnualInline):
    model = models.NotaAnualAvaliador


class NotaAnualHomologadorInline(NotaAnualInline):
    model = models.NotaAnualHomologador

    def get_initial(self):
        data = []
        if self.request.method == "GET" and not self.view.object:
            pontuacao_avaliador = (
                self.view.inscricao_pre_analise.pontuacoes_avaliadores.first()
            )
            for nota in pontuacao_avaliador.notas.all():
                data.append(
                    {
                        "ano": nota.ano,
                        "portugues": nota.portugues,
                        "historia": nota.historia,
                        "geografia": nota.geografia,
                        "matematica": nota.matematica,
                    }
                )
        return data


class CreatePontuacaoView(
    RevisionMixin, GroupRequiredMixin, extra_views.CreateWithInlinesView
):
    raise_exception = True

    def check_create_permission(self):
        return False

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.fase = get_object_or_404(
                models.FaseAjustePontuacao, pk=self.kwargs["fase_pk"]
            )
            self.inscricao_pre_analise = get_object_or_permission_denied(
                analise_models.InscricaoPreAnalise, pk=self.kwargs["inscricao_pk"]
            )
            if self.check_mailbox_duplicada():
                return False

            self.inscricao_original = self.inscricao_pre_analise.inscricao
            return self.check_create_permission()

        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = f"Pontuação da {self.inscricao_original}"
        data["nome_botao"] = "Salvar"
        data["inscricao"] = self.inscricao_pre_analise
        data["inscricao_original"] = self.inscricao_original
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_pontuacao_inscricao_psct")),
            ("Pontuação de inscrição", ""),
        )
        return data

    def get_initial(self):
        return {
            "inscricao_preanalise": self.inscricao_pre_analise,
            "inscricao": self.inscricao_original,
            "fase": self.fase,
            "ensino_regular": self.inscricao_original.pontuacao.ensino_regular,
        }

    def get_success_url(self):
        messages.info(self.request, "Pontuação salva com sucesso")


class UpdatePontuacaoView(
    RevisionMixin, GroupRequiredMixin, extra_views.UpdateWithInlinesView
):
    raise_exception = True

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.pontucao = get_object_or_404(self.model, pk=self.kwargs["pk"])
            self.fase = self.pontucao.fase
            self.inscricao_pre_analise = self.pontucao.inscricao_preanalise
            self.inscricao_original = self.pontucao.inscricao
            return self.pontucao.pode_alterar(self.request.user)
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = f"Pontuação da {self.inscricao_original}"
        data["nome_botao"] = "Salvar"
        data["inscricao"] = self.inscricao_pre_analise
        data["inscricao_original"] = self.inscricao_original
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_pontuacao_inscricao_psct")),
            ("Pontuação de inscrição", ""),
        )
        return data

    def get_success_url(self):
        messages.info(self.request, "Pontuação salva com sucesso")


class PontuacaoView(GroupRequiredMixin, generic.DetailView):
    raise_exception = True

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.pontuacao = get_object_or_permission_denied(
                self.model, pk=self.kwargs["pk"]
            )
            self.inscricao_pre_analise = self.pontuacao.inscricao_preanalise
            self.inscricao_original = self.pontuacao.inscricao
            return self.pontuacao.pode_ver(self.request.user)
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data["titulo"] = f"Pontuação da {self.inscricao_original}"
        data["inscricao"] = self.inscricao_pre_analise
        data["inscricao_original"] = self.inscricao_original
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_pontuacao_inscricao_psct")),
            (self.get_breadcrumb_title(), ""),
        )
        return data

    def get_breadcrumb_title(self):
        return ""


class CreatePontuacaoAvaliadorView(CreatePontuacaoView):
    model = models.PontuacaoAvaliador
    group_required = "Avaliador PSCT"
    template_name = "psct/pontuacao/pontuacaoavaliador.html"
    form_class = pontuacao_forms.PontuacaoAvaliadorForm
    inlines = [NotaAnualAvaliadorInline]

    def check_create_permission(self):
        return (
            self.inscricao_pre_analise.mailbox_pontuacao_avaliador.filter(
                avaliador=self.request.user
            ).exists()
            and (
                not self.inscricao_pre_analise.pontuacoes_avaliadores.filter(
                    avaliador=self.request.user
                ).exists()
            )
            and self.fase.acontecendo
        )

    def check_mailbox_duplicada(self):
        mb = models.MailboxPontuacaoAvaliador.objects.get(
            fase=self.fase, avaliador=self.request.user
        )
        return mb.pode_devolver(self.inscricao_pre_analise)

    def get_initial(self):
        initial = super().get_initial()
        initial["avaliador"] = self.request.user
        return initial

    def get_success_url(self):
        super().get_success_url()
        return reverse("list_pontuacao_inscricao_psct") + "?tab=aguardando_ajuste"


class UpdatePontuacaoAvaliadorView(UpdatePontuacaoView):
    model = models.PontuacaoAvaliador
    group_required = "Avaliador PSCT"
    template_name = "psct/pontuacao/pontuacaoavaliador.html"
    form_class = pontuacao_forms.PontuacaoAvaliadorForm
    inlines = [NotaAnualAvaliadorInline]

    def get_success_url(self):
        super().get_success_url()
        return reverse("list_pontuacao_inscricao_psct") + "?tab=aguardando_ajuste"


class PontuacaoAvaliadorView(PontuacaoView):
    model = models.PontuacaoAvaliador
    group_required = "Avaliador PSCT"
    template_name = "psct/pontuacao/pontuacaoavaliador_detail.html"

    def get_breadcrumb_title(self):
        return f"Pontuação do Avaliador #{self.pontuacao.pk}"


class CreateLoteHomologadorPontuacaoView(GroupRequiredMixin, generic.FormView):
    group_required = "Homologador PSCT"
    raise_exception = True
    form_class = forms.Form
    template_name = "psct/base/confirmacao.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.fase = get_object_or_404(
                models.FaseAjustePontuacao, pk=self.kwargs["fase_pk"]
            )

            if self.fase.eh_homologador(self.request.user):
                return not models.MailboxPontuacaoHomologador.possui_inscricao_pendente(
                    self.fase, self.request.user
                )
            return False
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data[
            "titulo"
        ] = "Deseja obter {} inscrições para homologação de ajuste?".format(
            self.kwargs["quantidade"]
        )
        data["back_url"] = reverse("list_pontuacao_inscricao_psct")
        data["nome_botao"] = "Confirmar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_pontuacao_inscricao_psct")),
            ("Obter Inscrições", ""),
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
            f"Foram adicionadas {quantidade} inscrições em sua caixa de avaliação",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("list_pontuacao_inscricao_psct") + "?tab=aguardando_homologacao"


class CreatePontuacaoHomologadorView(CreatePontuacaoView):
    model = models.PontuacaoHomologador
    group_required = "Homologador PSCT"
    template_name = "psct/pontuacao/pontuacaohomologador.html"
    form_class = pontuacao_forms.PontuacaoHomologadorForm
    inlines = [NotaAnualHomologadorInline]

    def check_create_permission(self):
        return (
            self.inscricao_pre_analise.mailbox_pontuacao_homologador.filter(
                homologador=self.request.user
            ).exists()
            and (
                not self.inscricao_pre_analise.pontuacoes_homologadores.filter(
                    homologador=self.request.user
                ).exists()
            )
            and self.fase.acontecendo
        )

    def check_mailbox_duplicada(self):
        mb = models.MailboxPontuacaoHomologador.objects.get(
            fase=self.fase, homologador=self.request.user
        )
        return mb.pode_devolver(self.inscricao_pre_analise)

    def get_initial(self):
        initial = super().get_initial()
        initial["homologador"] = self.request.user
        pontuacao_avaliador = self.inscricao_pre_analise.pontuacoes_avaliadores.first()
        if pontuacao_avaliador:
            initial["ensino_regular"] = pontuacao_avaliador.ensino_regular
        return initial

    def get_success_url(self):
        super().get_success_url()
        return reverse("list_pontuacao_inscricao_psct") + "?tab=aguardando_homologacao"

    def forms_valid(self, form, inlines):
        result = super().forms_valid(form, inlines)
        situacao = form.cleaned_data.get("situacao")
        if situacao:
            if situacao == "DEFERIR":
                self.object.deferir()
            else:
                self.object.indeferir()
        return result


class UpdatePontuacaoHomologadorView(UpdatePontuacaoView):
    model = models.PontuacaoHomologador
    group_required = "Homologador PSCT"
    template_name = "psct/pontuacao/pontuacaohomologador.html"
    form_class = pontuacao_forms.PontuacaoHomologadorForm
    inlines = [NotaAnualHomologadorInline]

    def get_success_url(self):
        super().get_success_url()
        return reverse("list_pontuacao_inscricao_psct") + "?tab=aguardando_homologacao"

    def forms_valid(self, form, inlines):
        result = super().forms_valid(form, inlines)
        situacao = form.cleaned_data.get("situacao")
        if situacao:
            if situacao == "DEFERIR":
                self.object.deferir()
            else:
                self.object.indeferir()
        return result


class PontuacaoHomologadorView(PontuacaoView):
    model = models.PontuacaoHomologador
    group_required = "Homologador PSCT"
    template_name = "psct/pontuacao/pontuacaohomologador_detail.html"

    def get_breadcrumb_title(self):
        return f"Pontuação do Homologador #{self.pontuacao.pk}"


class PontuacaoAdminView(GroupRequiredMixin, generic.DetailView):
    model = analise_models.InscricaoPreAnalise
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/pontuacao/pontuacaoadmin_detail.html"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.inscricao_pre_analise = get_object_or_404(
                analise_models.InscricaoPreAnalise, pk=self.kwargs["pk"]
            )
            self.inscricao_original = self.inscricao_pre_analise.inscricao
        return perm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data["titulo"] = f"Pontuação da {self.inscricao_original}"
        data["inscricao"] = self.inscricao_pre_analise
        data["inscricao_original"] = self.inscricao_original
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_pontuacao_inscricao_psct")), ("Pontuação", "")
        )
        return data


class RedistribuirInscricaoView(GroupRequiredMixin, generic.FormView):
    group_required = "Administradores PSCT"
    raise_exception = True
    template_name = "psct/base/display_form.html"
    redistribuidor_class = None
    form_class = RedistribuirForm
    group_name = None

    def dispatch(self, request, *args, **kwargs):
        self.fase = get_object_or_404(
            models.FaseAjustePontuacao, pk=self.kwargs["fase_pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Redistribuir Inscrições"
        data["nome_botao"] = "Redistribuir"
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_pontuacao_inscricao_psct")),
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
        return reverse("list_pontuacao_inscricao_psct")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["fase"] = self.fase
        return kwargs


class RedistribuirPontuacaoAvaliadorView(RedistribuirInscricaoView):
    redistribuidor_class = distribuicao.RedistribuirInscricaoAvaliador
    group_name = "Avaliador PSCT"


class RedistribuirPontuacaoHomologadorView(RedistribuirInscricaoView):
    redistribuidor_class = distribuicao.RedistribuirInscricaoHomologador
    group_name = "Homologador PSCT"


class DevolverInscricaoView(AnyGroupRequiredMixin, generic.FormView):
    group_required = ("Avaliador PSCT", "Homologador PSCT")
    raise_exception = True
    template_name = "psct/base/confirmacao.html"
    form_class = forms.Form
    mailbox_class = None

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.mb = get_object_or_404(
                self.mailbox_class, pk=self.kwargs["mailbox_pk"]
            )
            self.inscricao = get_object_or_404(
                analise_models.InscricaoPreAnalise, pk=self.kwargs["inscricao_pk"]
            )
            return self.mb.pode_devolver(self.inscricao)
        return False

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = f"Deseja realmente devolver a inscrição de {self.inscricao}?"
        data["nome_botao"] = "Devolver"
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_pontuacao_inscricao_psct")),
            ("Devolver Inscrição", ""),
        )
        return data

    def form_valid(self, form):
        messages.info(self.request, "Inscrição devolvida com sucesso!")
        self.mb.inscricoes.remove(self.inscricao)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("list_pontuacao_inscricao_psct")


class DevolverInscricaoAvaliadorView(DevolverInscricaoView):
    mailbox_class = models.MailboxPontuacaoAvaliador


class DevolverInscricaoHomologadorView(DevolverInscricaoView):
    mailbox_class = models.MailboxPontuacaoHomologador


class ImportarInscricaoView(GroupRequiredMixin, generic.FormView):
    raise_exception = True
    template_name = "psct/base/confirmacao.html"
    form_class = pontuacao_forms.ImportarForm
    group_required = "Administradores PSCT"

    def has_permission(self):
        perm = super().has_permission()
        if perm:
            self.fase = get_object_or_404(
                models.analise_models.FaseAnalise, pk=self.kwargs["fase_pk"]
            )
            if not self.fase.get_fase_ajuste():
                return False
        return perm

    def form_valid(self, form):
        indeferimento = form.cleaned_data["justificativa"]
        pilha, created = models.PilhaInscricaoAjuste.objects.get_or_create(
            fase=self.fase.ajuste_pontuacao
        )
        qs = analise_models.InscricaoPreAnalise.objects.filter(
            Q(
                avaliacoes_homologador__isnull=True,
                avaliacoes_avaliador__texto_indeferimento=indeferimento,
            )
            | Q(
                avaliacoes_homologador__isnull=False,
                avaliacoes_homologador__texto_indeferimento=indeferimento,
            ),
            fase=self.fase,
            situacao=analise_models.SituacaoInscricao.INDEFERIDA.name,
        )
        pilha.inscricoes.add(*qs)
        messages.success(self.request, "Inscrições importadas com suscesso")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["fase"] = self.fase
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Importar inscrições para ajuste"
        data["nome_botao"] = "Importar"
        data["back_url"] = reverse("list_pontuacao_inscricao_psct")
        data["breadcrumb"] = BreadCrumb.create(
            ("Inscrições", reverse("list_pontuacao_inscricao_psct")),
            ("Importar Inscrições", ""),
        )
        return data

    def get_success_url(self):
        return reverse("list_pontuacao_inscricao_psct")
