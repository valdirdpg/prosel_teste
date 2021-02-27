from datetime import datetime

from celery import Task
from celery.result import AsyncResult
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

from base.choices import BaseChoice


class StateChoice(BaseChoice):
    PENDING = "Aguardando"
    RECEIVED = "Recebida"
    STARTED = "Iniciada"
    SUCCESS = "Executada com sucesso"
    FAILURE = "Falha"
    REVOKED = "Cancelada"
    RETRY = "Aguardando nova tentativa"


class Job(models.Model):
    user = models.ForeignKey(User, verbose_name="Usuário", on_delete=models.CASCADE)
    task_id = models.CharField(verbose_name="Task ID", max_length=36, unique=True)
    name = models.CharField(verbose_name="Nome", max_length=255)
    state = models.CharField(
        verbose_name="Estado",
        max_length=10,
        choices=StateChoice.choices(),
        default=StateChoice.PENDING.name,
    )
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="Data de criação")
    end_time = models.DateTimeField(
        null=True, blank=True, verbose_name="Data de término"
    )

    class Meta:
        verbose_name_plural = "Jobs"
        verbose_name = "Job"
        ordering = ("-start_time",)

    @property
    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time

    def close(self):
        self.end_time = datetime.now()
        self.save()

    @property
    def task(self):
        return AsyncResult(self.task_id)

    @property
    def raw_state(self):
        return self.task.state

    def get_state(self):
        return StateChoice.label(self.raw_state)

    def get_result(self):
        task = self.task
        if task.ready():
            if task.state == StateChoice.SUCCESS.name:
                return task.result
            return {
                "message": "Erro ao executar a tarefa. Um email de notificação do problema foi enviado aos administradores.",
                "url": "/",
            }

    def has_result(self):
        return self.task.ready()

    @classmethod
    def new(cls, user, async_result, name):
        return cls.objects.create(user=user, task_id=async_result.id, name=name)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("wait_view", kwargs={"pk": self.pk})


class PortalTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self._job_update_state(task_id, StateChoice.FAILURE.name)

    def on_success(self, retval, task_id, args, kwargs):
        self._job_update_state(task_id, StateChoice.SUCCESS.name)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        Job.objects.filter(task_id=task_id).update(state=StateChoice.RETRY.name)

    def _job_update_state(self, task_id, state):
        Job.objects.filter(task_id=task_id).update(state=state, end_time=datetime.now())
