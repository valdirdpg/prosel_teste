from ajax_select.fields import AutoCompleteSelectField, AutoCompleteSelectMultipleField
from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction
from suaprest.django.auth import get_or_create_user, validate_users

from base.forms import Form, ModelForm
from editais.models import Edital
from psct.models import recurso as models
from psct.models.consulta import Coluna
from psct.tasks.recurso import distribuir_recursos


class RecursoForm(ModelForm):
    class Meta:
        model = models.Recurso
        exclude = []
        widgets = {
            "usuario": forms.HiddenInput,
            "inscricao": forms.HiddenInput,
            "fase": forms.HiddenInput,
        }


class RecursoGrupoForm(Form):
    nome = forms.CharField(label="Nome do Grupo")
    servidores = AutoCompleteSelectMultipleField(
        "servidores", required=False, help_text="Digite a matrícula ou nome do servidor"
    )
    grupos_merge = AutoCompleteSelectMultipleField(
        "grupos", required=False, label="Importar usuários dos grupos", help_text=""
    )
    grupos_exclude = AutoCompleteSelectMultipleField(
        "grupos", required=False, label="Excluir usuários dos grupos", help_text=""
    )

    def __init__(self, is_update=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_update = is_update

    def clean_nome(self):
        nome = self.cleaned_data.get("nome")
        if nome and Group.objects.filter(name=nome).exists() and not self.is_update:
            raise ValidationError("Já existe um grupo com esse nome")
        return nome

    def clean_servidores(self):
        matriculas = self.cleaned_data["servidores"]
        if matriculas:
            validate_users(matriculas)
        return matriculas


class UpdateRecursoGrupoForm(RecursoGrupoForm):
    edital = forms.ModelChoiceField(label="Edital", queryset=Edital.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = self.fields["edital"].queryset
        self.fields["edital"].queryset = qs.filter(processo_inscricao__isnull=False)


class AgruparRecursoForm(Form):
    criterio = forms.ModelChoiceField(
        label="Critério Utilizado para Agrupar Recursos",
        queryset=Coluna.objects.filter(
            entidade__app_label="psct", entidade__model="recurso"
        ),
    )


class DistribuirRecursoForm(Form):
    def __init__(self, fase, coluna, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fase = fase
        self.coluna = coluna
        valores = sorted(
            models.Recurso.objects.filter(fase=fase)
            .values_list(coluna.query_string, flat=True)
            .distinct()
        )

        grupos = self.get_grupos(fase.edital)

        for valor in valores:
            avaliador_key = f"avaliador_{valor}"
            sufixo_label = coluna.get_format()(valor)
            self.fields[avaliador_key] = forms.ModelChoiceField(
                queryset=grupos,
                required=False,
                label=f"Avaliadores excluídos de {sufixo_label}",
            )
            self.fields[avaliador_key].widget.attrs["class"] = "form-control"

            if fase.requer_homologador:
                homologador_key = f"homologador_{valor}"
                self.fields[homologador_key] = forms.ModelChoiceField(
                    queryset=grupos,
                    required=False,
                    label=f"Homologadores excluídos de {sufixo_label}",
                )
                self.fields[homologador_key].widget.attrs["class"] = "form-control"

    def get_grupos(self, edital):
        return Group.objects.filter(
            grupos_editais__isnull=False, grupos_editais__edital=edital
        ).distinct()

    def get_choices(self, fase):
        return [(g.id, g) for g in self.get_grupos(fase.edital)]

    def distribuir(self):

        avaliadores = {}
        homologadores = {}
        for field in self.fields:
            if field.startswith("avaliador_"):
                valor = field[len("avaliador_") :]
                grupo_exclusao = self.cleaned_data[field]
                g_id = self.get_grupo(
                    self.fase.avaliadores.grupo, valor, grupo_exclusao
                )
                avaliadores[valor] = g_id
            if field.startswith("homologador_"):
                valor = field[len("homologador_") :]
                grupo_exclusao = self.cleaned_data[field]
                g_id = self.get_grupo(
                    self.fase.homologadores.grupo, valor, grupo_exclusao
                )
                homologadores[valor] = g_id

        return distribuir_recursos.delay(
            self.fase.id, self.coluna.id, avaliadores, homologadores
        )

    def get_grupo(self, grupo, valor, grupo_exclusao):

        if not grupo_exclusao:
            return grupo.id

        nome = "{} ({}/{}) - {}".format(
            grupo.name,
            self.fase.edital.numero,
            self.fase.edital.ano,
            self.coluna.get_format()(valor),
        )
        novo_grupo, created = models.Group.objects.get_or_create(name=nome[:80])
        grupo_edital, created = models.GrupoEdital.objects.get_or_create(
            grupo=novo_grupo, edital=self.fase.edital
        )
        novo_grupo.user_set.clear()
        novo_grupo.user_set.add(*grupo.user_set.all())
        novo_grupo.user_set.remove(*grupo_exclusao.user_set.all())
        return novo_grupo.id

    def clean(self):
        super().clean()

        total_avaliadores = self.fase.avaliadores.grupo.user_set.count()

        for field in self.fields:
            grupo = self.cleaned_data.get(field)
            if not grupo:
                continue
            users = grupo.user_set.count()
            if grupo:
                if (
                    field.startswith("avaliador")
                    and (total_avaliadores - users) < self.fase.quantidade_avaliadores
                ):
                    raise ValidationError(
                        {
                            field: "O Grupo tem menos usuários do que a fase exige de avaliadores"
                        }
                    )
                if field.startswith("homologador") and not users:
                    raise ValidationError({field: "O Grupo está vazio"})


class ParecerAvaliadorForm(ModelForm):
    aceito = forms.ChoiceField(
        label="Situação", choices=models.SITUACAO_CHOICES, required=True
    )
    concluido = forms.ChoiceField(
        label="Enviar",
        choices=models.CONCLUIDO_CHOICES,
        required=True,
        help_text="O parecer não poderá mais ser editado e será entregue"
        " ao homologador.",
    )

    class Meta:
        model = models.ParecerAvaliador
        exclude = []
        widgets = {"avaliador": forms.HiddenInput, "recurso": forms.HiddenInput}


class ParecerHomologadorForm(ModelForm):
    aceito = forms.ChoiceField(
        label="Situação", choices=models.SITUACAO_CHOICES, required=True
    )

    class Meta:
        model = models.ParecerHomologador
        exclude = []
        widgets = {"homologador": forms.HiddenInput, "recurso": forms.HiddenInput}


class SubstituirForm(Form):
    servidor = AutoCompleteSelectField("servidores", help_text="", label="Servidor")

    def __init__(self, grupo, servidor_atual, grupo_permissao, *args, **kwargs):
        self.grupo = grupo
        self.servidor_atual = servidor_atual
        self.grupo_permissao = grupo_permissao
        super().__init__(*args, **kwargs)

    def clean_servidor(self):
        servidor = self.cleaned_data.get("servidor")
        if servidor:
            label_servidor = "{} ({}) - {}".format(
                servidor.nome, servidor.matricula, servidor.campus
            )
            if not self.grupo.user_set.filter(username=servidor.matricula).exists():
                raise ValidationError(
                    'O servidor "{}" não pertence ao grupo "{}"'.format(
                        label_servidor, self.grupo
                    )
                )
            user = self.get_user_servidor()
            if user == self.servidor_atual:
                raise ValidationError("Você não pode substituir pelo mesmo servidor")
            if not self.grupo_permissao.has_member(user):
                raise ValidationError(
                    '"{}" não é membro do grupo "{}"'.format(
                        label_servidor, self.grupo_permissao.name
                    )
                )
        return servidor

    def get_user_servidor(self):
        return models.User.objects.get(username=self.cleaned_data["servidor"].matricula)


class PermissionGroupForm(Form):
    servidores = AutoCompleteSelectMultipleField(
        "servidores", help_text="Digite a matrícula ou nome do  servidor"
    )

    def __init__(self, group, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = group

    def save(self):
        servidores = self.cleaned_data["servidores"]
        self.group.user_set.clear()
        users = [
            get_or_create_user(matricula, is_staff=False) for matricula in servidores
        ]
        self.group.user_set.add(*users)

    def clean_servidores(self):
        matriculas = self.cleaned_data["servidores"]
        if matriculas:
            validate_users(matriculas)
        return matriculas


class RedistribuirForm(Form):
    origem = AutoCompleteSelectField(
        "servidores", label="Servidor de Origem", help_text=""
    )
    destino = AutoCompleteSelectField(
        "servidores", label="Servidor de Destino", help_text=""
    )
    quantidade = forms.IntegerField(label="Quantidade de itens")

    def __init__(self, fase, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fase = fase

    def redistribuir(self, redistribuidor_class, group_name):
        origem = models.User.objects.get(username=self.cleaned_data["origem"].matricula)
        destino = models.User.objects.get(
            username=self.cleaned_data["destino"].matricula
        )
        quantidade = self.cleaned_data["quantidade"]

        with transaction.atomic():
            group = models.Group.objects.get(name=group_name)
            redistribuidor = redistribuidor_class(
                self.fase, origem, destino, quantidade
            )
            quantidade = redistribuidor.executar()
            destino.groups.add(group)
        return quantidade

    def clean_servidor(self, servidor):
        servidor = self.cleaned_data[servidor]
        if servidor:
            if not models.GrupoEdital.objects.filter(
                grupo__user__username=servidor.matricula
            ).exists():
                raise ValidationError(
                    f'O servidor "{servidor}" não pertence a nenhum grupo do sistema'
                )
        return servidor

    def clean_origem(self):
        return self.clean_servidor("origem")

    def clean_destino(self):
        return self.clean_servidor("destino")


class ImportarGrupoForm(Form):
    grupo_edital = forms.ModelChoiceField(
        models.GrupoEdital.objects.all(), label="Grupo"
    )


class ParecerAvaliadorAdminForm(ModelForm):
    concluido = forms.ChoiceField(
        label="Enviada",
        choices=models.CONCLUIDO_CHOICES,
        required=True,
        help_text="O parecer não poderá mais ser editado e será entregue"
        " ao homologador.",
    )

    class Meta:
        model = models.ParecerAvaliador
        fields = ["concluido"]

    def clean(self):
        recurso = self.instance.recurso
        if recurso and recurso.parecer:
            raise ValidationError(
                "Você não pode alterar o parecer pois o homologador já emitiu parecer"
            )
