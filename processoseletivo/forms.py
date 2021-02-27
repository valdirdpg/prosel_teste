from datetime import date

from ajax_select.fields import AutoCompleteSelectField
from dal import autocomplete
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from suaprest.django import get_or_create_user, validate_user
from django.contrib.admin.widgets import AdminDateWidget

from base.fields import ModelChoiceCustomLabelField
from base.forms import Form as BForm, ModelForm as BModelForm
from cursos.models import Campus
from editais import models as editais_models
from editais.choices import EventoCronogramaChoices
from processoseletivo import models


class PeriodoConvocacaoInlineForm(forms.ModelForm):
    class Meta:
        model = editais_models.PeriodoConvocacao
        exclude = ("tipo", "inscricao")


class PeriodoConvocacaoInlineFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = EventoCronogramaChoices.choices()

        for index, form in enumerate(self.forms):
            if index >= self.min_num:
                break
            if not form.instance.pk:
                form.fields["evento"].choices = [choices[index]]
                form.fields["nome"].initial = choices[index][1]

    def clean(self):
        interesse = False
        analise = False
        confirmacao = False
        erros = []
        eventos = []
        for form in self.forms:
            etapa = form.cleaned_data.get("etapa")
            evento = form.cleaned_data.get("evento")
            nome = form.cleaned_data.get("nome")
            interesse = interesse or (evento == "INTERESSE")
            analise = analise or (evento == "ANALISE")
            confirmacao = confirmacao or (evento == "CONFIRMACAO")

            if etapa.encerrada and form.has_changed():
                erros.append(
                    f"Etapa Encerrada: Não é permitido editar o Período de Convocação de nome {nome}"
                )
            if evento not in ("INTERESSE", "OUTRO") and evento in eventos:
                erros.append(
                    "Não pode haver mais de um Período de Convocação com o evento {}.".format(
                        EventoCronogramaChoices.label(evento)
                    )
                )

            eventos.append(evento)

        if not interesse:
            erros.append(
                "No Cronograma deve existir, pelo menos, 1 (UM) evento de Interesse de Matrícula."
            )
        if not analise:
            erros.append(
                "No Cronograma deve existir, pelo menos, 1 (UM) evento de Análise de Documentação."
            )
        if not confirmacao:
            erros.append(
                "No Cronograma deve existir, pelo menos, 1 (UM) evento de Confirmação de Matrícula."
            )
        if eventos.count("INTERESSE") > 2:
            erros.append(
                "No Cronograma devem existir, no máximo, 2 (DOIS) eventos de Interesse de Matrícula."
            )

        if erros:
            raise ValidationError(erros)


class AnaliseDocumentalForm(forms.ModelForm):
    confirmacao_interesse = AutoCompleteSelectField(
        "ps_confirmacoes", help_text="Digite o nome do candidato.", show_help_text=False
    )
    situacao_final = forms.ChoiceField(
        label="Situação final",
        widget=forms.RadioSelect,
        choices=models.SITUACAO_CHOICES,
    )

    def save(self, *args, **kwargs):
        self.instance.data = date.today()
        self.instance.servidor_coordenacao = self.user.username

        return super().save(*args, **kwargs)

    class Meta:
        model = models.AnaliseDocumental
        exclude = ("data", "servidor_coordenacao")
        widgets = {
            "confirmacao_interesse": autocomplete.ModelSelect2(
                url="autocomplete_confirmacao_interesse"
            )
        }


class TipoAnaliseForm(forms.ModelForm):
    situacao = forms.ChoiceField(
        label="Situação", widget=forms.RadioSelect, choices=models.SITUACAO_CHOICES
    )

    class Meta:
        model = models.TipoAnalise
        exclude = ()


class ConfirmacaoInteresseForm(forms.ModelForm):
    inscricao = AutoCompleteSelectField(
        "ps_inscricoes", help_text="Digite o nome do candidato", show_help_text=False
    )
    etapa = forms.ModelChoiceField(
        queryset=models.Etapa.objects.filter(encerrada=False),
        empty_label="-------------",
    )

    class Meta:
        model = models.ConfirmacaoInteresse
        exclude = ()
        widgets = {"inscricao": autocomplete.ModelSelect2(url="autocomplete_inscricao")}


class AvaliacaoDocumentalForm(BModelForm):
    class Meta:
        model = models.AvaliacaoDocumental
        fields = [
            "situacao",
            "observacao",
            "analise_documental",
            "data",
            "servidor_setor",
            "tipo_analise",
        ]
        widgets = {
            "analise_documental": forms.HiddenInput,
            "data": forms.HiddenInput,
            "servidor_setor": forms.HiddenInput,
            "tipo_analise": forms.HiddenInput,
        }
        labels = {
            "situacao": "Situação (Campo Obrigatório)",
            "observacao": "Observações",
        }
        help_texts = {
            "observacao": "Informe aqui as justificativas para o deferimento ou "
            "indeferimento da avaliação do aluno."
        }
        error_messages = {
            NON_FIELD_ERRORS: {
                "unique_together": "Já existe avaliação deste tipo cadastrada para esta inscrição."
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["situacao"].required = True


class AvaliacaoDocumentalUpdateForm(BModelForm):
    class Meta:
        model = models.AvaliacaoDocumental
        fields = ["situacao", "observacao"]
        labels = {"situacao": "Situação", "observacao": "Observações"}
        help_texts = {
            "observacao": "Informe as justificativas para o deferimento ou "
            "indeferimento da avaliação do aluno."
        }


class ServidorLotacaoForm(BForm):
    servidor = AutoCompleteSelectField(
        "servidores", label="Servidor", help_text="", required=True
    )
    campi = forms.MultipleChoiceField(
        label="Campi de Lotação",
        required=False,
        widget=forms.SelectMultiple(),
        help_text="Para desmarcar um item ou selecionar mais de 1(um) item, é necessário manter a tecla "
        '"Control" pressionada e clicar em cada um dos itens desejados. Se você estiver utilizando '
        'o sistema operacional macOS, substituir a tecla "Control" pela tecla "Command" na '
        "instrução anterior.",
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        super().__init__(*args, **kwargs)
        if request.user.is_superuser or models.is_sistemico(request.user):
            self.campi_choices = [(c.pk, c) for c in Campus.objects.all()]
        elif models.is_admin_campus(request.user):
            self.campi_choices = [(c.pk, c) for c in request.user.lotacoes.all()]
        else:
            self.campi_choices = []
        self.campi_choices_ids = [id for (id, value) in self.campi_choices]
        self.fields["campi"].choices = self.campi_choices
        self.fields["campi"].widget.attrs["size"] = len(self.campi_choices)

    def clean_servidor(self):
        servidor = self.cleaned_data["servidor"]
        if servidor:
            validate_user(servidor.matricula)
            return get_or_create_user(servidor.matricula, is_staff=False)
        return servidor

    def save(self):
        data = self.clean()
        servidor_username = data.get("servidor")
        servidor = User.objects.get(username=servidor_username)

        campi_marcados = Campus.objects.filter(id__in=data["campi"])
        servidor.lotacoes.add(*campi_marcados)

        if self.initial.get("campi", None):
            for c_id in self.initial["campi"]:
                if str(c_id) not in data["campi"] and c_id in self.campi_choices_ids:
                    campus = Campus.objects.get(pk=c_id)
                    servidor.lotacoes.remove(campus)


class RecursoForm(forms.ModelForm):
    analise_documental = AutoCompleteSelectField(
        "ps_analises", help_text="Digite o nome do candidato", show_help_text=False
    )

    class Meta:
        model = models.Recurso
        exclude = ()
        widgets = {
            "analise_documental": autocomplete.ModelSelect2(
                url="autocomplete_analise_documental"
            )
        }


class VagaForm(forms.ModelForm):
    candidato = AutoCompleteSelectField(
        "ps_candidatos", help_text="Digite o nome do candidato", show_help_text=False
    )

    class Meta:
        model = models.Vaga
        exclude = ()
        widgets = {"candidato": autocomplete.ModelSelect2(url="autocomplete_candidato")}


class ImportacaoForm(BForm):
    def __init__(self, *args, **kwargs):
        modalidades = kwargs.pop("modalidades")
        super().__init__(*args, **kwargs)

        def modalidade_str(modalidade):
            return modalidade.resumo if modalidade.resumo else modalidade.nome

        for index, modalidade in enumerate(modalidades):
            self.fields[f"field{index}"] = ModelChoiceCustomLabelField(
                label=modalidade,
                label_from_instance_func=modalidade_str,
                queryset=models.Modalidade.objects.all(),
            )
        self.styled_fields.append("__all__")
        self.apply_style()

    def save(self):
        for field, modalidade in self.cleaned_data.items():
            models.ModalidadeVariavel.objects.get_or_create(
                modalidade=modalidade, nome=self.fields[field].label
            )
