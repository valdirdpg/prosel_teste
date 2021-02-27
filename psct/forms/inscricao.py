from datetime import datetime
from decimal import Decimal

from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from form_utils import forms as forms_utils

from editais.models import Edital
from processoseletivo.models import ModalidadeEnum
from psct.models import inscricao as models, RespostaCriterio

ALERTA_APAGAR_NOTAS = (
    "Atenção, você está modificando sua forma de ingresso e as notas já inseridas serão apagadas. "
    "Clique em continuar para apagar as notas inseridas."
)


class ModalidadeChoiceField(forms.ModelChoiceField):

    def __init__(self, queryset, edital, *args, **kwargs):
        self.edital = edital
        super().__init__(queryset, *args, **kwargs)

    def label_from_instance(self, obj):
        return obj.por_nivel_formacao(self.edital.processo_inscricao)


class InscricaoForm(forms_utils.BetterModelForm):
    campus = forms.ModelChoiceField(
        models.c_models.Campus.objects.filter(cursonocampus__isnull=False)
        .order_by("nome")
        .distinct(),
        label="Campus",
        help_text="-",
    )
    cotista = forms.ChoiceField(
        label="Conforme edital, toda/o candidata/o, mesmo cotista, concorre às vagas da Ampla Concorrência.Confirme sua opção:",
        choices=[("SIM", "Desejo concorrer pela Ampla Concorrência e pela cota definida abaixo."), ("NAO", "Desejo concorrer apenas pela Ampla Concorrência.")],
        widget=forms.widgets.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["curso"].label = "Primeira opção de curso"
        self.fields["aceite"].required = True
        self.fields["aceite"].initial = False
        if "edital" in kwargs["initial"]:
            edital = kwargs["initial"]["edital"]
        else:
            edital = kwargs["instance"].edital

        resposta_pcd = RespostaCriterio.objects.get(resposta_modelo__candidato=kwargs["initial"]["candidato"],resposta_modelo__modelo__edital=edital,criterio_alternativa_selecionada__criterio__id = 9)
        resposta_baixa_renda = RespostaCriterio.objects.get(resposta_modelo__candidato=kwargs["initial"]["candidato"],resposta_modelo__modelo__edital=edital,criterio_alternativa_selecionada__criterio__id = 1)
        resposta_ppi = RespostaCriterio.objects.get(resposta_modelo__candidato=kwargs["initial"]["candidato"],resposta_modelo__modelo__edital=edital,criterio_alternativa_selecionada__criterio__id = 2)
        resposta_escola_publica_fund = RespostaCriterio.objects.get(resposta_modelo__candidato=kwargs["initial"]["candidato"],resposta_modelo__modelo__edital=edital,criterio_alternativa_selecionada__criterio__id = 10)
        resposta_escola_publica_med = RespostaCriterio.objects.filter(resposta_modelo__candidato=kwargs["initial"]["candidato"],resposta_modelo__modelo__edital=edital,criterio_alternativa_selecionada__criterio__id = 11)

        marcou_pcd = resposta_pcd.criterio_alternativa_selecionada.posicao == 2
        marcou_baixa_renda = resposta_baixa_renda.criterio_alternativa_selecionada.posicao == 1
        marcou_ppi = resposta_ppi.criterio_alternativa_selecionada.posicao in [1, 2, 4]
        marcou_escola_publica_fund = resposta_escola_publica_fund.criterio_alternativa_selecionada.posicao == 1
        if resposta_escola_publica_med:
            marcou_escola_publica_med = resposta_escola_publica_med[0].criterio_alternativa_selecionada.posicao == 1

        if resposta_escola_publica_med:
            marcou_escola_publica = marcou_escola_publica_med and marcou_escola_publica_fund
        else:
            marcou_escola_publica = marcou_escola_publica_fund

        self.fields["modalidade_cota"] = ModalidadeChoiceField(
            models.Modalidade.objects.ordenação_por_tipo_escola().order_by("texto"),
            edital=edital,
            label="CONFIRME O TIPO DE VAGA A CONCORRER:",
            required=False,
            widget=forms.widgets.RadioSelect,
            empty_label=None,
            help_text="<p>A modalidade de vaga marcada abaixo corresponde às informações prestadas por você. </p><p>Confirme se a descrição marcada corresponde à sua realidade e se você poderá comprovar.Caso contrário, clique em Voltar e corrija suas informações.</p> <p>Os aprovadas/os deverão comprovar documentalmente todas as condições informadas.</p>",
        )
        is_cotista = False
        if marcou_escola_publica and marcou_baixa_renda and marcou_ppi and marcou_pcd:
            self.fields["modalidade_cota"].initial = 2
            is_cotista=True
        elif marcou_escola_publica and marcou_baixa_renda and marcou_ppi:
            self.fields["modalidade_cota"].initial = 8
            is_cotista = True
        elif marcou_escola_publica and marcou_baixa_renda and marcou_pcd:
            self.fields["modalidade_cota"].initial = 9
            is_cotista = True
        elif marcou_escola_publica and marcou_baixa_renda:
            self.fields["modalidade_cota"].initial = 6
            is_cotista = True
        elif marcou_escola_publica and marcou_ppi and marcou_pcd:
            self.fields["modalidade_cota"].initial = 10
            is_cotista = True
        elif marcou_escola_publica and marcou_ppi:
            self.fields["modalidade_cota"].initial = 5
            is_cotista = True
        elif marcou_escola_publica and marcou_pcd:
            self.fields["modalidade_cota"].initial = 11
            is_cotista = True
        elif marcou_escola_publica:
            self.fields["modalidade_cota"].initial = 7
            is_cotista = True
        elif marcou_pcd:
            self.fields["modalidade_cota"].initial = 4
            is_cotista = True

        radio_and_select_fields = ["cotista", "modalidade_cota","aceite"]
        for field in self.fields:
            if field not in radio_and_select_fields:
                self.fields[field].widget.attrs["class"] = "form-control"

        if "edital" in kwargs["initial"]:
            cursos = kwargs["initial"]["edital"].processo_inscricao.cursos.all()
        elif "instance" in kwargs:
            obj = kwargs["instance"]
            cursos = obj.edital.processo_inscricao.cursos.filter(
                formacao=obj.curso.formacao
            )
        else:
            cursos = models.c_models.CursoSelecao.objects.none()

        if "curso" in self.fields:
            self.fields["curso"].label_from_instance = models.format_curso
            self.fields["curso"].queryset = cursos.order_by("curso__nome")

        if "campus" in self.fields:
            self.fields["campus"].queryset = (
                models.c_models.Campus.objects.filter(cursonocampus__in=cursos)
                .distinct()
                .order_by("nome")
            )

        if kwargs.get("instance") and "campus" in self.fields:
            instance = kwargs["instance"]
            self.fields["campus"].initial = instance.curso.campus
            if instance.modalidade_cota.id != ModalidadeEnum.ampla_concorrencia or (
                hasattr(self, "data") and is_cotista):
                cotista = "SIM"
            else:
                cotista = "NAO"
            if is_cotista:
                cotista = "SIM"
            self.fields["cotista"].initial = cotista

    def clean_modalidade_cota(self):
        cotista = self.cleaned_data.get("cotista")
        modalidade_cota = self.cleaned_data.get("modalidade_cota")
        if cotista and cotista == "SIM" and not modalidade_cota:
            raise ValidationError(
                "Você deve selecionar a modalidade da cota que gostaria concorrer ou "
                "marcar a opção de não concorrer por cota."
            )
        if cotista and cotista == "NAO":
            modalidade_cota = models.Modalidade.objects.get(id=ModalidadeEnum.ampla_concorrencia)
        return modalidade_cota

    def style_fields(self, *fields):
        fields_to_style = set(fields).intersection(set(self.fields.keys()))
        for field in fields_to_style:
            self.fields[field].widget.attrs["class"] = "form-control"

    @staticmethod
    def get_cursos_queryset(**kwargs):
        if "edital" in kwargs["initial"]:
            cursos = kwargs["initial"]["edital"].processo_inscricao.cursos.all()
        elif "instance" in kwargs:
            obj = kwargs["instance"]
            cursos = obj.edital.processo_inscricao.cursos.all()
        else:
            cursos = models.c_models.CursoSelecao.objects.none()
        return cursos

    class Meta:
        model = models.Inscricao
        fields = [
            "candidato",
            "edital",
            "cotista",
            "modalidade_cota",
            "campus",
            "curso",
            "aceite",
        ]
        widgets = {"candidato": forms.HiddenInput, "edital": forms.HiddenInput}

class InscricaoSegundaOpcaoTecnicoForm(InscricaoForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cursos = self.get_cursos_queryset(**kwargs)
        self.fields["curso_segunda_opcao"].queryset = cursos.order_by("curso__nome")
        self.fields["curso_segunda_opcao"].label = "Segunda opção de curso"
        # if kwargs.get("instance") and "curso_segunda_opcao" in self.fields:
        #     instance = kwargs["instance"]
        #     print('>> oi {}'.format(instance.inscricao.curso_segunda_opcao))
        #     self.fields["curso_segunda_opcao"].initial = instance.inscricao.curso_segunda_opcao

    def clean(self):
        super().clean()
        cleaned_data = self.cleaned_data
        curso = cleaned_data.get("curso")
        curso_segunda_opcao = cleaned_data.get("curso_segunda_opcao")
        if curso and curso_segunda_opcao and curso_segunda_opcao == curso:
            self.add_error(
                "curso_segunda_opcao",
                "A segunda opção de curso deve ser diferente da primeira opção.",
            )
        com_segunda_opcao = cleaned_data.get("com_segunda_opcao")
        if com_segunda_opcao and not curso_segunda_opcao:
            self.add_error(
                "curso_segunda_opcao",
                "Este campo é obrigatório porque você "
                "optou por ter uma segunda opção de curso.",
            )
        # if not com_segunda_opcao and curso_segunda_opcao:
        #     del cleaned_data["curso_segunda_opcao"]
        return cleaned_data

    class Meta(InscricaoForm.Meta):
        fields = [
            "candidato",
            "edital",
            "cotista",
            "modalidade_cota",
            "campus",
            "curso",
            # "com_segunda_opcao",
            "curso_segunda_opcao",
            "aceite",
        ]

class InscricaoGraduacaoForm(forms_utils.BetterModelForm):
    cotista = forms.ChoiceField(
        label="Deseja concorrer dentro das cotas ou é portador de deficiência?",
        choices=[("SIM", "Sim"), ("NAO", "Não")],
        widget=forms.widgets.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["curso"].label = "Primeira opção de curso"
        self.fields["aceite"].required = True
        self.fields["aceite"].initial = False
        if "edital" in kwargs["initial"]:
            edital = kwargs["initial"]["edital"]
        else:
            edital = kwargs["instance"].edital
        self.fields["modalidade_cota"] = ModalidadeChoiceField(
            models.Modalidade.objects.ordenação_por_tipo_escola(),
            edital=edital,
            label="Modalidade da cota",
            required=False,
            widget=forms.widgets.RadioSelect,
            empty_label=None
        )
        self.style_fields("curso")
        cursos = self.get_cursos_queryset(**kwargs)
        self.fields["curso"].queryset = cursos.order_by("curso__nome")

        if kwargs.get("instance"):
            instance = kwargs["instance"]
            if not instance.modalidade_cota.is_ampla or (
                hasattr(self, "data") and self.data.get("cotista") == "SIM"
            ):
                cotista = "SIM"
            else:
                cotista = "NAO"
            self.fields["cotista"].initial = cotista

    def style_fields(self, *fields):
        fields_to_style = set(fields).intersection(set(self.fields.keys()))
        for field in fields_to_style:
            self.fields[field].widget.attrs["class"] = "form-control"

    @staticmethod
    def get_cursos_queryset(**kwargs):
        if "edital" in kwargs["initial"]:
            cursos = kwargs["initial"]["edital"].processo_inscricao.cursos.all()
        elif "instance" in kwargs:
            obj = kwargs["instance"]
            cursos = obj.edital.processo_inscricao.cursos.all()
        else:
            cursos = models.c_models.CursoSelecao.objects.none()
        return cursos

    def clean_modalidade_cota(self):
        cotista = self.cleaned_data.get("cotista")
        modalidade_cota = self.cleaned_data.get("modalidade_cota")
        if cotista and cotista == "SIM" and not modalidade_cota:
            raise ValidationError(
                "Você deve selecionar a modalidade da cota que gostaria concorrer ou "
                "marcar a opção de não concorrer por cota."
            )
        if cotista and cotista == "NAO":
            modalidade_cota = models.Modalidade.objects.get(id=ModalidadeEnum.ampla_concorrencia)
        return modalidade_cota

    class Meta:
        model = models.Inscricao
        fields = [
            "candidato",
            "edital",
            "curso",
            "cotista",
            "modalidade_cota",
            "aceite",
        ]
        widgets = {
            "candidato": forms.HiddenInput,
            "edital": forms.HiddenInput,
        }


class InscricaoSegundaOpcaoGraduacaoForm(InscricaoGraduacaoForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cursos = self.get_cursos_queryset(**kwargs)
        self.fields["curso_segunda_opcao"].queryset = cursos.order_by("curso__nome")
        self.fields["curso_segunda_opcao"].label = "Segunda opção de curso"
        self.style_fields("curso", "curso_segunda_opcao")

    def clean(self):
        super().clean()
        cleaned_data = self.cleaned_data
        curso = cleaned_data.get("curso")
        curso_segunda_opcao = cleaned_data.get("curso_segunda_opcao")
        if curso and curso_segunda_opcao and curso_segunda_opcao == curso:
            self.add_error(
                "curso_segunda_opcao",
                "A segunda opção de curso deve ser diferente da primeira opção.",
            )
        com_segunda_opcao = cleaned_data.get("com_segunda_opcao")
        if com_segunda_opcao and not curso_segunda_opcao:
            self.add_error(
                "curso_segunda_opcao",
                "Este campo é obrigatório porque você "
                "optou por ter uma segunda opção de curso.",
            )
        if not com_segunda_opcao and curso_segunda_opcao:
            del cleaned_data["curso_segunda_opcao"]
        return cleaned_data

    class Meta(InscricaoGraduacaoForm.Meta):
        fields = [
            "candidato",
            "edital",
            "curso",
            "com_segunda_opcao",
            "curso_segunda_opcao",
            "cotista",
            "modalidade_cota",
            "aceite",
        ]

class InscricaoFormAutocomplete(forms_utils.BetterModelForm):
    class Meta:
        model = models.Inscricao
        exclude = ()
        widgets = {
            "candidato": autocomplete.ModelSelect2(url="autocomplete-candidato-psct")
        }


class ComprovanteForm(forms_utils.BetterModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nome"].widget.attrs["class"] = "form-control"

    class Meta:
        model = models.Comprovante
        fields = ["inscricao", "nome", "arquivo"]
        widgets = {"inscricao": forms.HiddenInput}


class BaseNotaForm(forms_utils.BetterModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        radio_and_select_fields = []
        for field in self.fields:
            if field not in radio_and_select_fields:
                self.fields[field].widget.attrs["class"] = "form-control"

    def clean_nota(self, disciplina):
        valor = self.cleaned_data.get(disciplina)
        if valor is not None and not Decimal("0.0") <= valor <= Decimal("10.0"):
            raise ValidationError(
                "O valor da nota não pode ser inferior a 0,0 ou superior a 10,0."
            )
        return valor

    def clean_portugues(self):
        return self.clean_nota("portugues")

    def clean_matematica(self):
        return self.clean_nota("matematica")

    def clean_historia(self):
        return self.clean_nota("historia")

    def clean_geografia(self):
        return self.clean_nota("geografia")


class NotaAnualForm(BaseNotaForm):
    ano = forms.IntegerField(label="Ano", disabled=True)

    class Meta:
        model = models.NotaAnual
        exclude = []


class SupletivoForm(BaseNotaForm):
    class Meta:
        model = models.NotaAnual
        exclude = []


class EnsinoRegularForm(forms.Form):
    ENSINO_INTEGRADO_CHOICES = [
        (
            "ENSINO_REGULAR",
            "Com as médias do 6º, 7º e 8º ano do Ensino Fundamental II.",
        ),
        (
            "OUTROS",
            "Com médias obtidas por outro meio ( supletivo, EJA, PROEJA, ENCCEJA  e etc.)",
        ),
    ]
    ENSINO_SUBSEQUENTE_CHOICES = [
        ("ENSINO_REGULAR", "Com as médias do 1º e 2º ano do Ensino Médio."),
        ("OUTROS", "Com médias obtidas por outro meio (ENEM, Supletivo, etc.)."),
    ]
    ensino = forms.ChoiceField(
        label="Desejo concorrer:",
        widget=forms.widgets.RadioSelect,
        choices=ENSINO_INTEGRADO_CHOICES,
        #initial="",
    )
    force = forms.BooleanField(widget=forms.HiddenInput, required=False)

    def __init__(self, pontuacao, is_edit=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pontuacao = pontuacao
        if pontuacao.inscricao.curso.formacao == "INTEGRADO" or pontuacao.inscricao.curso.formacao == "CONCOMITANTE":
            self.fields["ensino"].choices = self.ENSINO_INTEGRADO_CHOICES
        else:
            self.fields["ensino"].choices = self.ENSINO_SUBSEQUENTE_CHOICES

        if not is_edit:
            self.fields["ensino"].initial = "NONE"
        else:
            if pontuacao.ensino_regular:
                self.fields["ensino"].initial = "ENSINO_REGULAR"
            else:
                self.fields["ensino"].initial = "OUTROS"

    def clean(self):
        super().clean()
        ensino = self.cleaned_data.get("ensino")
        force = self.cleaned_data.get("force")
        if ensino:
            if self.pontuacao.notas.exists() and not force:
                error = False
                if ensino == "ENSINO_REGULAR" and not self.pontuacao.ensino_regular:
                    error = True
                if ensino == "OUTROS" and self.pontuacao.ensino_regular:
                    error = True
                if error:
                    self.data = self.data.copy()
                    self.data["force"] = True
                    raise ValidationError(ALERTA_APAGAR_NOTAS)
        return self.cleaned_data


class ProcessoInscricaoForm(forms.ModelForm):
    class Meta:
        model = models.ProcessoInscricao
        exclude = []

    def clean(self):
        cursos = self.cleaned_data.get("cursos")
        formacao = self.cleaned_data.get("formacao")
        formacoes_aceitas_graduacao = ["TECNOLOGICO", "BACHARELADO", "LICENCIATURA"]

        if formacao and formacao != models.ProcessoInscricao.GRADUACAO:
            if cursos and cursos.exclude(formacao=formacao).exists():
                raise ValidationError(
                    {
                        "cursos": (
                            "Você escolheu cursos de formações diferentes da "                            
                            "que você selecionou para o processo."
                        )
                    }
                )
        elif (
            cursos and cursos.exclude(formacao__in=formacoes_aceitas_graduacao).exists()
        ):
            raise ValidationError(
                {
                    "cursos": (
                        "Você escolheu cursos de formações diferentes da "                            
                        "que você selecionou para o processo."
                    )
                }
            )
        return self.cleaned_data


class ComprovantesFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        forms_valids = len([f for f in self.forms if f.is_valid() and f.cleaned_data])
        if forms_valids - len(self.deleted_forms) < 1:
            raise ValidationError(
                "Você deve enviar no mínimo 1 e no máximo 5 comprovantes."
            )

    def full_clean(self):
        super().full_clean()
        if self._non_form_errors:
            self._non_form_errors = self.error_class(
                ["Você deve enviar no mínimo 1 e no máximo 5 comprovantes."]
            )


class ModalidadeVagaForm(forms.ModelForm):
    modalidade = forms.ModelChoiceField(
        label="Modalidade", queryset=models.Modalidade.objects.all()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def format_modalidade(obj):
            return obj.equivalente.resumo if obj.equivalente.resumo else obj.equivalente

        self.fields["modalidade"].label_from_instance = format_modalidade

    class Meta:
        model = models.ModalidadeVagaCursoEdital
        exclude = []


class ModalidadeVagaInlineFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        modalidades = list(models.Modalidade.objects.all())

        def format_(obj):
            return obj.equivalente.resumo if obj.equivalente.resumo else obj.equivalente

        for index, form in enumerate(self.forms):
            if not form.instance.pk and modalidades:
                modalidade = modalidades[index]
                form.fields["modalidade"].choices = [
                    (modalidade.id, format_(modalidade))
                ]

    def clean(self):
        lista = []
        for form in self.forms:
            if form.cleaned_data and "DELETE" not in form.changed_data:
                modalidade = form.cleaned_data.get("modalidade")
                quantidade_vagas = form.cleaned_data.get("quantidade_vagas")
                if not modalidade and quantidade_vagas:
                    raise ValidationError("Não é possível cadastrar modalidade vazia.")

                if modalidade in lista:
                    raise ValidationError(
                        "Não é possível cadastrar duas vezes a mesma modalidade."
                    )
                else:
                    lista.append(form.cleaned_data.get("modalidade"))


class CursoEditalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["edital"].queryset = (
            self.fields["edital"]
            .queryset.filter(processo_inscricao__isnull=False)
            .distinct()
            .order_by("-id")
        )
        self.fields["curso"].queryset = (
            self.fields["curso"]
            .queryset.filter(processoinscricao__isnull=False)
            .distinct()
            .order_by("formacao", "curso__nome", "modalidade", "campus__nome", "polo__cidade__nome")
        )

    class Meta:
        model = models.CursoEdital
        fields = ("edital", "curso")


class ImportarNotasEnemForm(forms_utils.BetterForm):
    edital = forms.ModelChoiceField(label="Edital", queryset=Edital.objects.none())
    ano = forms.ChoiceField(label="Ano de referência",)
    arquivo = forms.FileField(label="Arquivo de notas", help_text="Arquivo no formato .csv")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"

        ano_atual = datetime.now().year
        self.fields["ano"].choices = (
                [("", "Selecione o ano de referencia")] +
                [(str(ano), str(ano)) for ano in range(ano_atual - 4, ano_atual + 1)]
        )
        self.fields["edital"].queryset = Edital.objects.filter(processo_inscricao__isnull=False)
