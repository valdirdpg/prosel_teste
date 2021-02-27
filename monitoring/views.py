from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic

from base.custom.datatypes import BreadCrumb
from base.custom.views import ListView
from base.custom.views.decorators import column, menu, tab
from monitoring.models import Job
from monitoring.templatetags.monitoring_tags import format_state


class ListJobView(LoginRequiredMixin, ListView):
    raise_exception = True
    list_display = (
        "id",
        "name",
        "user_display",
        "start_time_display",
        "end_time_display",
        "state_display",
        "acoes",
    )
    tabs = ["minhas", "todas"]
    model = Job

    def get_breadcrumb(self):
        return (("Lista de Tarefas", ""),)

    def get_title(self):
        return "Lista de tarefas"

    def get_tabs(self):
        if self.request.user.is_superuser:
            return super().get_tabs()
        return ["minhas"]

    @column("Usuário")
    def user_display(self, obj):
        return f"{obj.user.get_full_name()} ({obj.user.username})"

    @column("Data de criação")
    def start_time_display(self, obj):
        return self._format_date(obj.start_time)

    @column("Data de término")
    def end_time_display(self, obj):
        return self._format_date(obj.end_time)

    @column("Estado", mark_safe=True)
    def state_display(self, obj):
        return format_state(obj.state)

    @menu("Opções", col="Ações")
    def acoes(self, menu_obj, obj):
        menu_obj.add(
            "Acompanhar progresso", reverse("wait_view", kwargs={"pk": obj.pk})
        )

    @tab(name="Minhas tarefas")
    def minhas(self, queryset):
        return queryset.filter(user=self.request.user)

    @tab(name="Todas")
    def todas(self, queryset):
        return queryset

    def _format_date(self, date):
        if date:
            return date.strftime("%d/%m/%Y %H:%M")
        return "-"


class WaitView(UserPassesTestMixin, generic.DetailView):
    template_name = "monitoring/wait.html"
    model = Job
    raise_exception = True

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["breadcrumb"] = BreadCrumb.create(("Execução de tarefa", ""))
        return data

    def test_func(self):
        self.object = self.get_object()
        return self.object.user == self.request.user


class AjaxCheckView(LoginRequiredMixin, generic.View):
    def get(self, request, *args, **kwargs):
        job = get_object_or_404(Job, pk=self.kwargs["pk"])
        if job.user != request.user:
            raise PermissionDenied()
        result = {"state": job.raw_state, "verbose_state": job.get_state()}
        if job.has_result():
            result["result"] = job.get_result()

        return JsonResponse(result)
