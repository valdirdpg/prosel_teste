from ajax_select.fields import AutoCompleteSelectField
from dal import autocomplete
from django import forms
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from form_utils import forms as forms_utils
from suaprest.django import get_or_create_user, validate_user, validate_users

import base.choices
from base.fields import ModelMultipleChoiceField
from base.forms import Form, ModelForm
from base.validators import cpf_validator
from processoseletivo.models import ProcessoSeletivo
from . import choices
from . import models


def modalidade_choices():
    return choices.Modalidade.choices(blank=True, empty_label="Todas as modalidades")


def formacao_choices():
    return choices.Formacao.choices(blank=True, empty_label="Todas as formações")


def nivel_formacao_choices():
    return choices.NivelFormacao.choices(blank=True, empty_label="Todos os níveis")


def turno_choices():
    return base.choices.Turno.choices(blank=True, empty_label="Todos os turnos")


class CursosSearchForm(Form):
    field_class = "form-control input-sm"
    cidade = forms.ModelChoiceField(
        label="Cidade",
        queryset=models.Cidade.objects.all().order_by("nome"),
        empty_label="Todas as Cidades",
        required=False,
    )
    modalidade = forms.ChoiceField(
        label="Modalidade", choices=modalidade_choices(), required=False
    )
    nome = forms.CharField(label="Nome ou palavras-chave", required=False)
    turno = forms.ChoiceField(label="Turno", choices=turno_choices(), required=False)
    formacao = forms.ChoiceField(
        label="Formação", choices=formacao_choices(), required=False
    )
    nivel_formacao = forms.ChoiceField(
        label="Nível de Formação", choices=nivel_formacao_choices(), required=False
    )
    forma_acesso = forms.ModelChoiceField(
        label="Forma de Acesso",
        queryset=ProcessoSeletivo.objects.all(),
        empty_label="Todas as formas de acesso",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nome"].widget.attrs["placeholder"] = "Nome ou palavras-chave"


class CampusForm(forms.ModelForm):
    servidores = ModelMultipleChoiceField(
        queryset=User.objects.all().order_by("first_name", "last_name"),
        widget=autocomplete.ModelSelect2Multiple(
            url="autocomplete_user", attrs={"data-minimum-input-length": 3}
        ),
        label_from_instance_func=lambda s: f"{s.get_full_name()} ({s.username})",
        required=False,
        help_text="Adicionar os servidores que poderão gerenciar as chamadas da pré-matrícula.",
    )

    class Meta:
        model = models.Campus
        exclude = ()
        widgets = {
            "diretor_ensino": autocomplete.ModelSelect2(url="autocomplete_servidor"),
            "diretor_ensino_substituto": autocomplete.ModelSelect2(
                url="autocomplete_servidor"
            ),
        }

    def __init__(self, *args, **kwargs):
        if kwargs.get("instance") is not None and kwargs["instance"].pk:
            initial = kwargs.get("initial", {})
            kwargs["initial"] = initial
        super().__init__(*args, **kwargs)
        self.fields["telefone"].widget.attrs["class"] = "mask-telefone"
        self.fields["mapa"].widget.attrs["placeholder"] = '<iframe src="..." ...>'

    def clean_servidores(self):
        matriculas = self.cleaned_data["servidores"]
        if matriculas:
            validate_users(matriculas)
        return matriculas


class DisciplinaCurso(forms.ModelForm):
    disciplina = AutoCompleteSelectField(
        "c_disciplinas", help_text="Digite o nome da disciplina", show_help_text=False
    )

    class Meta:
        model = models.DisciplinaCurso
        exclude = ()
        widgets = {
            "disciplina": autocomplete.ModelSelect2(url="autocomplete_disciplina"),
            "docentes": autocomplete.ModelSelect2Multiple(url="autocomplete_docente"),
        }

    def clean_plano(self):
        super().clean()
        plano = self.cleaned_data.get("plano")
        if not plano:
            raise ValidationError("Você deve informar um plano para a disciplina.")
        else:
            return self.cleaned_data["plano"]


class CoordenacaoForm(forms.ModelForm):
    docente = AutoCompleteSelectField(
        "c_docentes", help_text="Digite o nome do professor", show_help_text=False, required=False
    )

    class Meta:
        model = models.Coordenacao
        exclude = ()
        widgets = {
            "coordenador": autocomplete.ModelSelect2(url="autocomplete_servidor"),
            "substituto": autocomplete.ModelSelect2(url="autocomplete_servidor"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["telefone"].widget.attrs["class"] = "mask-telefone"


class PoloForm(forms.ModelForm):
    class Meta:
        model = models.Polo
        exclude = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["telefone"].widget.attrs["class"] = "mask-telefone"


class CursoForm(forms.ModelForm):
    nivel_formacao = forms.ChoiceField(
        required=True,
        label="Nível de Formação",
        choices=choices.NivelFormacao.choices(),
    )

    class Meta:
        model = models.Curso
        exclude = ()


class CursoNoCampusForm(forms.ModelForm):
    conceito_nao_se_aplica = forms.BooleanField(required=False, label="Não se aplica")
    codigo_nao_se_aplica = forms.BooleanField(
        required=False, label="Código e-MEC não se aplica"
    )
    cpc_nao_se_aplica = forms.BooleanField(required=False, label="Não se aplica")
    enade_nao_se_aplica = forms.BooleanField(required=False, label="Não se aplica")
    ch_estagio_nao_se_aplica = forms.BooleanField(required=False, label="Não se aplica")
    ch_tcc_nao_se_aplica = forms.BooleanField(required=False, label="Não se aplica")
    ch_rel_estagio_nao_se_aplica = forms.BooleanField(
        required=False, label="Não se aplica"
    )
    ch_pratica_docente_nao_se_aplica = forms.BooleanField(
        required=False, label="Não se aplica"
    )
    ch_atividades_comp_nao_se_aplica = forms.BooleanField(
        required=False, label="Não se aplica"
    )
    periodo_min_int_nao_se_aplica = forms.BooleanField(
        required=False, label="Não se aplica"
    )

    class Meta:
        model = models.CursoSelecao
        exclude = ("disciplinas_atualizacao", "ch_total")
        widgets = {"forma_acesso": forms.CheckboxSelectMultiple}

    def clean(self):
        conceitos_validos = ["1", "2", "3", "4", "5"]
        cleaned_data = super().clean()
        conceito = cleaned_data.get("conceito")
        conceito_nao_se_aplica = cleaned_data.get("conceito_nao_se_aplica")
        codigo = cleaned_data.get("codigo")
        codigo_nao_se_aplica = cleaned_data.get("codigo_nao_se_aplica")
        cpc = cleaned_data.get("cpc")
        cpc_nao_se_aplica = cleaned_data.get("cpc_nao_se_aplica")
        enade = cleaned_data.get("enade")
        enade_nao_se_aplica = cleaned_data.get("enade_nao_se_aplica")
        ch_estagio = cleaned_data.get("ch_estagio")
        ch_estagio_nao_se_aplica = cleaned_data.get("ch_estagio_nao_se_aplica")
        ch_tcc = cleaned_data.get("ch_tcc")
        ch_tcc_nao_se_aplica = cleaned_data.get("ch_tcc_nao_se_aplica")
        ch_rel_estagio = cleaned_data.get("ch_rel_estagio")
        ch_rel_estagio_nao_se_aplica = cleaned_data.get("ch_rel_estagio_nao_se_aplica")
        ch_pratica_docente = cleaned_data.get("ch_pratica_docente")
        ch_pratica_docente_nao_se_aplica = cleaned_data.get(
            "ch_pratica_docente_nao_se_aplica"
        )
        ch_atividades_comp = cleaned_data.get("ch_atividades_comp")
        ch_atividades_comp_nao_se_aplica = cleaned_data.get(
            "ch_atividades_comp_nao_se_aplica"
        )
        periodo_min_int = cleaned_data.get("periodo_min_int")
        periodo_min_int_nao_se_aplica = cleaned_data.get(
            "periodo_min_int_nao_se_aplica"
        )

        if conceito not in conceitos_validos and not conceito_nao_se_aplica:
            msg = 'Conceito inválido. Insira um conceito no intervalo entre 1 e 5, ou marque a opção "Não se aplica".'
            self.add_error("conceito", msg)

        if not codigo_nao_se_aplica and not codigo:
            self.add_error(
                "codigo",
                'Código inválido. Insira um código ou marque a opção "Não se aplica".',
            )

        if not cpc_nao_se_aplica and not cpc:
            self.add_error(
                "cpc",
                'CPC inválido. Insira um valor ou marque a opção "Não se aplica".',
            )

        if not enade_nao_se_aplica and not enade:
            self.add_error(
                "enade",
                'Valor inválido. Insira um valor ou marque a opção "Não se aplica".',
            )

        if not ch_estagio_nao_se_aplica and not ch_estagio:
            self.add_error(
                "ch_estagio",
                'Horas inválidas. Insira um valor ou marque a opção "Não se aplica".',
            )

        if not ch_tcc_nao_se_aplica and not ch_tcc:
            self.add_error(
                "ch_tcc",
                'Valor inválido. Insira um valor ou marque a opção "Não se aplica".',
            )

        if not ch_rel_estagio_nao_se_aplica and not ch_rel_estagio:
            self.add_error(
                "ch_rel_estagio",
                'Valor inválido. Insira um valor ou marque a opção "Não se aplica".',
            )

        if not ch_pratica_docente_nao_se_aplica and not ch_pratica_docente:
            self.add_error(
                "ch_pratica_docente",
                'Valor inválido. Insira um valor ou marque a opção "Não se aplica".',
            )

        if not ch_atividades_comp_nao_se_aplica and not ch_atividades_comp:
            self.add_error(
                "ch_atividades_comp",
                'Valor inválido. Insira um valor ou marque a opção "Não se aplica".',
            )

        if not periodo_min_int_nao_se_aplica and not periodo_min_int:
            self.add_error(
                "ch_atividades_comp",
                'Valor inválido. Insira um valor ou marque a opção "Não se aplica".',
            )


class CursoNoCampusUpdateForm(forms_utils.BetterModelForm):
    class Meta:
        model = models.CursoNoCampus
        fields = ("perfil_libras", "video_catalogo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"


class ObrigatorioInlineFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()
        curso_no_campus = self.forms[0].cleaned_data.get("curso")
        if curso_no_campus and curso_no_campus.publicado:
            forms_persistidos = 0
            for form in self.forms:
                if form.cleaned_data and "DELETE" not in form.changed_data:
                    forms_persistidos += 1
            if forms_persistidos == 0:
                raise ValidationError(
                    f"Deve haver, no mínimo, 1 {self.model._meta.verbose_name} "
                    "para que o curso seja publicado."
                )


class DocumentoInlineFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()
        curso_no_campus = self.forms[0].cleaned_data.get("curso")
        if curso_no_campus and curso_no_campus.publicado:
            tipos_documentos = set()
            for form in self.forms:
                if form.cleaned_data:
                    tipo_documento = form.cleaned_data.get("tipo")
                    if "DELETE" not in form.changed_data:
                        tipos_documentos.add(tipo_documento)
            lista_erros = []
            for t in curso_no_campus.documentos_obrigatorios():
                if t not in tipos_documentos:
                    lista_erros.append(
                        [f"Deve haver, no mínimo, 1(um) documento do tipo {t.nome}."]
                    )
            if lista_erros:
                raise ValidationError(lista_erros)


class DisciplinaInlineFormSet(ObrigatorioInlineFormSet):
    def get_queryset(self):
        return super().get_queryset().order_by("periodo", "disciplina")


class DocenteExternoForm(forms.ModelForm):
    matricula = forms.CharField(
        label="CPF",
        max_length=11,
        validators=[cpf_validator],
        required=True,
        help_text="Apenas números (não é necessário '.' ou '-')",
    )

    class Meta:
        model = models.DocenteExterno
        fields = ("nome", "matricula", "lattes", "titulacao")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["titulacao"].required = True
        self.fields["lattes"].required = True


class ServidorCreateForm(ModelForm):
    servidor_suap = AutoCompleteSelectField(
        "servidores", label="Servidor", required=True, show_help_text=False
    )

    field_order = ["servidor_suap", "tipo", "titulacao", "lattes"]

    class Meta:
        model = models.Servidor
        fields = ["tipo", "titulacao", "lattes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo"].choices = [
            (base.choices.TipoServidor.TAE.name, base.choices.TipoServidor.TAE.value),
            (
                base.choices.TipoServidor.DOCENTE.name,
                base.choices.TipoServidor.DOCENTE.value,
            ),
        ]

    def clean_servidor_suap(self):
        servidor_suap = self.cleaned_data["servidor_suap"]
        if servidor_suap:
            validate_user(servidor_suap.matricula)
            if models.Servidor.objects.filter(
                matricula=servidor_suap.matricula
            ).exists():
                self.add_error("servidor_suap", "Este servidor já existe.")
        return servidor_suap

    def clean(self):
        msg_erro_campo_obrigatorio = (
            "Este campo deve ser informado para servidores docentes."
        )
        tipo = self.cleaned_data.get("tipo")
        titulacao = self.cleaned_data.get("titulacao", None)
        lattes = self.cleaned_data.get("lattes", None)
        if tipo == base.choices.TipoServidor.DOCENTE.name:
            if not titulacao:
                self.add_error("titulacao", msg_erro_campo_obrigatorio)
            if not lattes:
                self.add_error("lattes", msg_erro_campo_obrigatorio)
        return super().clean()

    def save(self):
        servidor_suap = self.cleaned_data.get("servidor_suap")
        self.instance.nome = servidor_suap.nome
        self.instance.matricula = servidor_suap.matricula
        user = get_or_create_user(servidor_suap.matricula, is_staff=False)
        return super().save()


class ServidorUpdateForm(ModelForm):
    class Meta:
        model = models.Servidor
        fields = ["titulacao", "lattes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.is_docente:
            self.fields["titulacao"].required = True
            self.fields["lattes"].required = True


class UsuarioCampusForm(Form):
    servidor = AutoCompleteSelectField(
        "servidores", label="Servidor", help_text="", required=True
    )

    def __init__(self, *args, **kwargs):
        self.campus = kwargs.pop("campus")
        super().__init__(*args, **kwargs)

    def clean_servidor(self):
        servidor = self.cleaned_data["servidor"]
        if servidor:
            validate_user(servidor.matricula)
        return servidor

    def save(self):
        data = self.clean()
        servidor_suap = data.get("servidor")
        servidor = get_or_create_user(servidor_suap.matricula, is_staff=True)
        servidor.lotacoes.add(self.campus)


class GerenciarPermissoesUsuarioCampusForm(Form):
    permissoes = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        label="Permissões disponíveis",
        widget=forms.SelectMultiple(),
        help_text=(
            "Para desmarcar um item ou selecionar mais de 1(um) item, é necessário manter a tecla "
            '"Control" pressionada e clicar em cada um dos itens desejados. Se você estiver '
            'utilizando o sistema operacional macOS, substituir a tecla "Control" pela tecla '
            '"Command" na instrução anterior.'
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop("usuario")
        self.grupos_gerenciados = kwargs.pop("grupos_gerenciados")
        super().__init__(*args, **kwargs)
        self.fields["permissoes"].queryset = Group.objects.filter(
            name__in=self.grupos_gerenciados
        )

    def save(self):
        permissoes = self.cleaned_data.get("permissoes")
        grupos_removidos = Group.objects.filter(name__in=self.grupos_gerenciados)
        grupos_removidos = grupos_removidos.difference(permissoes)
        if grupos_removidos:
            self.usuario.groups.remove(*grupos_removidos)
        if permissoes:
            self.usuario.groups.add(*permissoes)
            grupos_staff = Group.objects.filter(
                name__in=[
                    "Administradores de Chamadas por Campi",
                    "Administradores de Cursos nos Campi",
                ]
            )
            if permissoes.intersection(grupos_staff).exists():
                self.usuario.is_staff = True
                self.usuario.save()
