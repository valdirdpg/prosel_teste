from collections import OrderedDict

from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.mail import mail_admins
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic, View
from django.views.generic.edit import FormMixin
from suaprest import SuapError
from suaprest.django import SUAPDjangoClient as Client

from base.custom.datatypes import BreadCrumb
from base.custom.views import ListView
from base.custom.views.decorators import column, menu
from base.custom.views.mixin import GroupRequiredMixin, UserPermissionsListMixin
from base.utils import human_list
from registration import utils
from . import choices
from . import forms
from . import models


class CursoListView(FormMixin, generic.ListView):
    model = models.CursoNoCampus
    form_class = forms.CursosSearchForm
    template_name = "cursos/curso_list.html"
    context_object_name = "cursos"
    ordering = ["curso__nome"]
    allow_empty = True

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["titulo"] = "Cursos do IFBA"
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.request.method == "GET":
            kwargs.update({"data": self.request.GET})
        return kwargs

    def get_queryset(self):
        form = self.get_form()
        if not form.is_valid():
            messages.error(
                self.request,
                "A URL está mal formada. Por favor, utilize o formulário de "
                "busca para localizar o curso desejado.",
            )
            qs = super().get_queryset().none()
        else:
            nivel_formacao = form.data.get("nivel_formacao", None)
            if nivel_formacao == "TECNICO":
                self.queryset = self.model.cursos_tecnicos
            elif nivel_formacao == "GRADUACAO":
                self.queryset = self.model.cursos_superiores
            elif nivel_formacao == "POSGRADUACAO":
                self.queryset = self.model.cursos_pos_graduacao
            qs = super().get_queryset().filter(excluido=False)

            cidade = form.data.get("cidade", None)
            if cidade:
                try:
                    id_cidade = int(cidade)
                    cidade_campus = Q(campus__cidade=id_cidade)
                    cidade_polo = Q(vagacurso__polo__cidade=id_cidade)
                    qs = qs.filter(cidade_campus | cidade_polo).distinct()
                except ValueError:
                    qs = qs.none()

            modalidade = form.data.get("modalidade", None)
            if modalidade:
                qs = qs.filter(modalidade=modalidade)

            nome = form.data.get("nome", None)
            if nome:
                curso_nome = Q(curso__nome__icontains=nome)
                curso_chaves = Q(palavras_chave__palavra__icontains=nome)
                qs = qs.filter(curso_nome | curso_chaves).distinct()

            formacao = form.data.get("formacao", None)
            if formacao:
                qs = qs.filter(formacao=formacao)

            turno = form.data.get("turno", None)
            if turno:
                qs = qs.filter(turno=turno)

            forma_acesso = form.data.get("forma_acesso", None)
            if forma_acesso:
                try:
                    id_forma_acesso = int(forma_acesso)
                    qs = qs.filter(forma_acesso=id_forma_acesso)
                except ValueError:
                    qs = qs.none()
            
        return qs.filter(cursoselecao__polo__isnull=True).distinct()


class CursoView(generic.TemplateView):
    template_name = "cursos/curso_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso_pk = int(self.kwargs["pk"])
        curso = get_object_or_404(models.CursoNoCampus, pk=curso_pk)
        periodos = curso.disciplinacurso_set.values_list(
            "periodo", flat=True
        ).distinct()
        periodos = sorted(periodos)
        disciplinas = OrderedDict()
        for n in periodos:
            disciplinas[n] = curso.disciplinacurso_set.filter(periodo=n).order_by(
                "disciplina"
            )

        docs = curso.documento_set.all().order_by("tipo")
        tipos = models.TipoDocumento.objects.filter(
            documento__curso=curso.id
        ).distinct()
        documentos = {}
        for t in tipos:
            documentos[t.nome] = docs.filter(tipo=t)

        context["curso"] = curso
        context["disciplinas"] = disciplinas
        context["documentos"] = documentos

        context["pode_editar_curso"] = utils.is_admin_sistemico_cursos(
            self.request.user
        )

        if curso.is_presencial:
            if models.VagaCurso.objects.filter(curso=curso).exists():
                vagas = models.VagaCurso.objects.filter(curso=curso).aggregate(
                    sum_s1=Sum("vagas_s1"), sum_s2=Sum("vagas_s2")
                )
                context["vagas"] = vagas["sum_s1"] + vagas["sum_s2"]
            else:
                context["vagas"] = 0

        return context


class CursoNoCampusUpdateView(GroupRequiredMixin, generic.UpdateView):
    form_class = forms.CursoNoCampusUpdateForm
    group_required = "Administradores Sistêmicos de Cursos"
    model = models.CursoNoCampus
    raise_exception = True
    template_name = "reuse/display_form.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data()
        titulo = f"Editar curso {self.object}"
        data["titulo"] = titulo
        data["breadcrumb"] = BreadCrumb.create(
            ("Cursos", reverse("cursos")),
            (f"{self.object}", reverse("curso", args=[self.object.id])),
            ("Editar", ""),
        )
        return data

    def get_success_url(self):
        messages.success(self.request, "Curso atualizado com sucesso.")
        return reverse("curso", args=[self.object.id])


class ContactView(generic.TemplateView):
    template_name = "cursos/contact_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pk = int(self.kwargs["pk"])
        tipo = self.kwargs["tipo"]

        if tipo == "polo":
            polo = get_object_or_404(models.Polo, id=pk)
            context["lugar"] = polo
            cursos = models.CursoNoCampus.objects.filter(
                vagacurso__polo=polo.pk
            ).order_by("curso__nome")
            context["cursos"] = cursos
        elif tipo == "campus":
            campus = get_object_or_404(models.Campus, id=pk)
            context["lugar"] = campus
            cursos = models.CursoNoCampus.objects.filter(campus=campus.pk).order_by(
                "curso__nome"
            )
            context["cursos"] = cursos

        context["tipo"] = tipo

        return context


class ContactListView(generic.TemplateView):
    template_name = "cursos/contact.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        campi = models.Campus.objects.all().order_by("nome")
        polos = models.Polo.objects.all().order_by("cidade__nome")

        context["campi"] = campi
        context["polos"] = polos

        return context


class ImportarDocentesView(GroupRequiredMixin, View):
    login_url = "/admin/login/"
    group_required = "Administradores Sistêmicos de Cursos"
    raise_exception = True

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            client = Client()
            response = client.get_docentes()
            for professor_id, professor in response.items():
                try:
                    obj = models.Docente.objects.get(matricula=professor["matricula"])
                except models.Servidor.DoesNotExist:
                    obj = models.Docente()
                professor.pop(
                    "titulacao"
                )  # titulação não será importada do Suap, será cadastrada aqui no portal.
                obj.__dict__.update(professor)
                if obj.lattes:
                    obj.lattes = "http://lattes.cnpq.br/" + obj.lattes
                if obj.rt == "40":
                    obj.rt = choices.RegimeTrabalho.TI.name
                elif obj.rt == "20":
                    obj.rt = choices.RegimeTrabalho.TP.name
                elif obj.rt == "99":
                    obj.rt = choices.RegimeTrabalho.DE.name
                obj.save()
            messages.info(request, "Docentes importados do SUAP com sucesso.")
        except SuapError as error:
            messages.error(
                request,
                "Ocorreu algum erro com a importação dos docentes. "
                "Um e-mail foi enviado para os administradores do sistema.",
            )
            mail_admins(
                subject="[Portal do Estudante / IFPB] Erro na importação de docentes do Suap",
                message=error.response.text,
            )

        return redirect("admin:cursos_servidor_changelist")


class AutoCompleteServidor(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    docente = False

    def get_queryset(self):
        if self.docente:
            qs = (
                models.Servidor.objects.docentes()
                | models.Servidor.objects.docentes_externos()
            )
        else:
            qs = models.Servidor.objects.all()

        if self.q:
            qs = qs.filter(Q(nome__icontains=self.q) | Q(matricula__istartswith=self.q))

        return qs.order_by("nome")


class AutoCompleteDisciplina(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = models.Disciplina.objects.all()

        if self.q:
            qs = qs.filter(nome__istartswith=self.q)

        return qs.order_by("nome")


class AutoCompleteUser(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = User.objects.all()

        if self.q:
            qs = qs.filter(
                Q(username__icontains=self.q)
                | Q(first_name__icontains=self.q)
                | Q(last_name__icontains=self.q)
                | Q(email__icontains=self.q)
            )

        return qs.order_by("first_name", "last_name")

    def get_result_label(self, result):
        """Return the label of a result."""
        return f"{result.get_full_name()} - ({result.username})"


class ServidorMixin:
    group_required = ["Administradores Sistêmicos de Cursos", "Diretores de Ensino"]
    model = models.Servidor
    raise_exception = True
    success_url = reverse_lazy("servidor_changelist")


class ServidorListView(ServidorMixin, GroupRequiredMixin, ListView):
    list_display = ("nome", "matricula", "tipo_display", "acoes")
    ordering = ["nome", "matricula"]
    template_name = "reuse/listview.html"

    @column("Tipo")
    def tipo_display(self, obj):
        return obj.get_tipo_display()

    @menu("Opções", col="Ações")
    def acoes(self, menu_obj: ListView.menu_class, obj: models.Servidor) -> None:
        menu_obj.add(
            "Editar servidor", reverse("servidor_change", kwargs=dict(pk=obj.id))
        )

    def get_breadcrumb(self):
        return ((self.get_title(), ""),)

    def get_button_area(self):
        menu_class = self.get_menu_class()
        menu_adicionar = menu_class("Adicionar", button_css="success")
        menu_adicionar.add("Novo servidor", reverse("servidor_add"))
        return [menu_adicionar]

    def get_queryset(self):
        return super().get_queryset().efetivos()


class ServidorCreateView(ServidorMixin, GroupRequiredMixin, generic.CreateView):
    form_class = forms.ServidorCreateForm
    template_name = "reuse/display_form.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        titulo = f"Adicionar novo {self.model._meta.verbose_name.lower()}"
        data["titulo"] = titulo
        data["nome_botao"] = "Salvar"
        data["breadcrumb"] = BreadCrumb.create(
            (self.model._meta.verbose_name_plural, self.success_url), (titulo, "")
        )
        return data

    def form_valid(self, form):
        messages.success(
            self.request, f"{self.model._meta.verbose_name} criado com sucesso."
        )
        return super().form_valid(form)


class ServidorUpdateView(ServidorMixin, GroupRequiredMixin, generic.UpdateView):
    form_class = forms.ServidorUpdateForm
    template_name = "reuse/display_form.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        titulo = (
            f"Editar servidor {self.object.get_tipo_display().lower()} {self.object}"
        )
        data["titulo"] = titulo
        data["nome_botao"] = "Salvar"
        data["breadcrumb"] = BreadCrumb.create(
            (self.model._meta.verbose_name_plural, self.success_url), (titulo, "")
        )
        return data

    def form_valid(self, form):
        messages.success(
            self.request, f"O servidor {self.object} foi atualizado com sucesso."
        )
        return super().form_valid(form)


class DiretorCampusPermissionMixin(GroupRequiredMixin):
    group_required = ["Diretores de Ensino"]

    def get_group_required(self):
        group_required = super().get_group_required()
        if "Diretores de Ensino" not in group_required:
            group_required.append("Diretores de Ensino")
        return group_required

    def has_permission(self):
        if self.request.user.is_superuser:
            return True
        if not self.diretor or not self.campus.eh_diretor(self.diretor):
            return False
        return super().has_permission()

    def setup(self, request, *args, **kwargs):
        self.campus = get_object_or_404(models.Campus, pk=kwargs.get("pk_campus"))
        self.diretor = models.Servidor.get_by_user(request.user)
        return super().setup(request, *args, **kwargs)


class PermissoesUsuariosCampusListView(
    DiretorCampusPermissionMixin, UserPermissionsListMixin, ListView
):
    grupos_gerenciados = (
        "Administradores de Chamadas por Campi",
        "Administradores de Cursos nos Campi",
        "Médicos",
        "Operador CAEST",
    )
    list_display = ["usuario", "permissoes", "acoes"]
    raise_exception = True

    @menu("Opções", col="Ações")
    def acoes(self, menu_obj: ListView.menu_class, obj: User) -> None:
        if not obj.is_superuser:
            menu_obj.add(
                "Gerenciar permissoes",
                reverse(
                    "gerenciar_permissoes_usuario_campus",
                    kwargs=dict(pk_campus=self.campus.id, pk_user=obj.id),
                ),
            )
        menu_obj.add(
            "Remover servidor",
            reverse(
                "remover_usuario_campus",
                kwargs=dict(pk_campus=self.campus.id, pk_user=obj.id),
            ),
        )

    def get_button_area(self):
        menu_class = self.get_menu_class()
        menu_adicionar = menu_class("Adicionar", button_css="success")
        menu_adicionar.add(
            "Novo usuário", reverse("adicionar_usuario_campus", args=[self.campus.id])
        )
        return [menu_adicionar]

    def get_breadcrumb(self):
        return (
            ("Admin", reverse("admin:index")),
            ("Cursos", reverse("admin:app_list", args=["cursos"])),
            ("Campi", reverse("admin:cursos_campus_changelist")),
            (
                f"{self.campus}",
                reverse("admin:cursos_campus_change", args=[self.campus.id]),
            ),
            ("Permissões dos servidores do campus", ""),
        )

    def get_queryset(self):
        return super().get_queryset().filter(lotacoes=self.campus).distinct()

    def get_title(self):
        return f"Permissões dos servidores do campus {self.campus}"


class AdicionarUsuarioCampusView(DiretorCampusPermissionMixin, generic.FormView):
    form_class = forms.UsuarioCampusForm
    raise_exception = True
    template_name = "reuse/display_form.html"

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Usuário criado com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        titulo = f"Adicionar novo usuário/servidor no campus {self.campus}"
        data["titulo"] = titulo
        data["nome_botao"] = "Salvar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Admin", reverse("admin:index")),
            ("Cursos", reverse("admin:app_list", args=["cursos"])),
            ("Campi", reverse("admin:cursos_campus_changelist")),
            (
                f"{self.campus}",
                reverse("admin:cursos_campus_change", args=[self.campus.id]),
            ),
            ("Permissões", self.get_success_url()),
            (titulo, ""),
        )
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["campus"] = self.campus
        return kwargs

    def get_success_url(self):
        return reverse("permissoes_campus", args=[self.campus.id])


class RemoverUsuarioCampusView(DiretorCampusPermissionMixin, generic.FormView):
    form_class = forms.forms.Form
    raise_exception = True
    template_name = "reuse/confirmacao.html"

    def form_valid(self, form):
        self.usuario.lotacoes.remove(self.campus)
        messages.success(self.request, "Usuário removido com sucesso.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        titulo = f"Remover usuário {self.usuario} no campus {self.campus}"
        data["titulo"] = titulo
        data["nome_botao"] = "Confirmar"
        data["extra_message"] = "Deseja realmente remover o usuário deste campus?"
        data["breadcrumb"] = BreadCrumb.create(
            ("Admin", reverse("admin:index")),
            ("Cursos", reverse("admin:app_list", args=["cursos"])),
            ("Campi", reverse("admin:cursos_campus_changelist")),
            (
                f"{self.campus}",
                reverse("admin:cursos_campus_change", args=[self.campus.id]),
            ),
            ("Permissões", reverse("permissoes_campus", args=[self.campus.id])),
            (titulo, ""),
        )
        return data

    def get_success_url(self):
        return reverse("permissoes_campus", args=[self.campus.id])

    def setup(self, request, *args, **kwargs):
        self.usuario = get_object_or_404(User, pk=kwargs.get("pk_user"))
        return super().setup(request, *args, **kwargs)


class GerenciarPermissaoUsuarioCampusView(
    DiretorCampusPermissionMixin, generic.FormView
):
    form_class = forms.GerenciarPermissoesUsuarioCampusForm
    grupos_gerenciados = (
        "Administradores de Chamadas por Campi",
        "Administradores de Cursos nos Campi",
        "Médicos",
        "Operador CAEST",
    )
    raise_exception = True
    template_name = "reuse/display_form.html"

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            f"As permissões do usuário {self.usuario.get_full_name()} ({self.usuario.username}) "
            f"foram atualizadas com sucesso.",
        )
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        outras_lotacoes = self.usuario.lotacoes.exclude(pk=self.campus.id)
        if outras_lotacoes:
            campi = human_list([x for x in outras_lotacoes])
            plural = outras_lotacoes.count() > 1
            mensagem = (
                f'Este usuário(a) também está associado(a) ao{"s" if plural else ""} '
                f'camp{"i" if plural else "us"} {campi}. Certifique-se que as alterações serão '
                f'consentidas por seu{"s" if plural else ""} respectivo{"s" if plural else ""} '
                f'diretor{"es" if plural else ""} de ensino.'
            )
            messages.warning(request, mensagem)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        titulo = f"Gerenciar permissões de {self.usuario.get_full_name()} ({self.usuario.username})"
        data["titulo"] = titulo
        data["nome_botao"] = "Salvar"
        data["breadcrumb"] = BreadCrumb.create(
            ("Admin", reverse("admin:index")),
            ("Cursos", reverse("admin:app_list", args=["cursos"])),
            ("Campi", reverse("admin:cursos_campus_changelist")),
            (
                f"{self.campus}",
                reverse("admin:cursos_campus_change", args=[self.campus.id]),
            ),
            ("Permissões", self.get_success_url()),
            (titulo, ""),
        )
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.usuario
        kwargs["grupos_gerenciados"] = self.grupos_gerenciados
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        if not initial:
            initial = {}
        initial["permissoes"] = self.usuario.groups.all()
        return initial

    def get_success_url(self):
        return reverse("permissoes_campus", args=[self.campus.id])

    def setup(self, request, *args, **kwargs):
        self.usuario = get_object_or_404(User, pk=kwargs.get("pk_user"))
        return super().setup(request, *args, **kwargs)
