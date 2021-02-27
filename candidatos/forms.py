from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from form_utils import forms as forms_utils

from base import choices
from base import models as base_models
from base.utils import is_maior_idade, TituloEleitor
from candidatos import models


class DadosBasicosForm(forms_utils.BetterModelForm):
    declara_veracidade = forms.BooleanField(
        label="DECLARO, para os fins de direito, sob as penas da lei, que as informações que apresento "
        "para o cadastro, são fiéis à verdade e condizentes com a realidade dos fatos. Fico ciente, "
        "portanto, que a falsidade desta declaração configura-se em crime previsto no Código Penal "
        "Brasileiro e passível de apuração na forma da Lei.",
        required=True,
    )
    email_confirm = forms.EmailField(max_length=55, label="Confirma E-mail")

    class Meta:
        model = base_models.PessoaFisica
        exclude = [
            "nome_social",
            "tipo_sanguineo",
            "profissao",
            "nome_mae",
            "nome_pai",
            "nacionalidade_old",
            "email_responsavel",
            "rg",
            "orgao_expeditor",
            "orgao_expeditor_uf",
            "data_expedicao",
            "certidao_tipo",
            "certidao",
            "certidao_folha",
            "certidao_livro",
            "certidao_data",
            "numero_titulo_eleitor",
            "zona_titulo_eleitor",
            "secao_titulo_eleitor",
            "data_emissao_titulo_eleitor",
            "uf_titulo_eleitor",
            "telefone2",
        ]

        labels = {
            "zona_titulo_eleitor": "Zona",
            "secao_titulo_eleitor": "Seção",
            "data_emissao_titulo_eleitor": "Data de Emissão",
            "uf_titulo_eleitor": "Estado Emissor",
            "naturalidade": "Município de Nascimento",
            "naturalidade_uf": "Estado de Nascimento",
            "uf": "Estado",
            "telefone": "Telefone",
        }

        help_texts = {
            "cpf": "Utilize somente o CPF do/a estudante candidato/a.",
            "nascimento": "Formato DD/MM/AAAA. Ex.: 25/12/1995",
            "naturalidade": "Obrigatório para brasileiros.",
            "naturalidade_uf": "Obrigatório para brasileiros.",
            "nome_responsavel": "Obrigatório para menores de 18 anos.",
            "parentesco_responsavel": "Obrigatório para menores de 18 anos.",
            "logradouro": "Ex.: Rua, Avenida, Sítio, etc.",
            "complemento_endereco": "Ex.: Casa B, Apto 301, etc.",
            "cep": "Formato NN.NNN-NNN (Ex.: 58.000-300)",
            "telefone": "Ex.: 83 3601 0000, ou 83 99999 0000",
        }

        fieldsets = (
            (
                "dados_gerais",
                {
                    "legend": "Informações Básicas",
                    "fields": (
                        "cpf",
                        "nome",
                        "nascimento",
                        "sexo",
                        "nacionalidade",
                        "naturalidade",
                        "naturalidade_uf",
                        "nome_responsavel",
                        "parentesco_responsavel",
                        "user",
                    ),
                },
            ),
            (
                "endereco",
                {
                    "legend": "Endereço",
                    "fields": (
                        "logradouro",
                        "numero_endereco",
                        "complemento_endereco",
                        "bairro",
                        "municipio",
                        "uf",
                        "cep",
                        "tipo_zona_residencial",
                    ),
                },
            ),
            (
                "contatos",
                {
                    "legend": "Informações para Contatos",
                    "fields": ("telefone", "email", "email_confirm"),
                },
            ),
        )

        row_attrs = {
            "cpf": {"class": "mask-cpf"},
            "nascimento": {"class": "has-feedback mask-data vDateField"},
            "cep": {"class": "mask-cep"},
            "telefone": {"class": "mask-telefone"},
            "email_confirm": {"class": "disablecopypaste"},
            "password_confirm": {"class": "disablecopypaste"},
        }

    class Media:
        js = ("js/utils.js", "js/responsaveis.js", "js/titulo_eleitor.js", "js/scripts.js")

    def __init__(self, *args, **kwargs):
        # Obriga o Candidato a sempre clicar no CheckBox quando atualizar os dados
        initial = {"declara_veracidade": False}

        instance = kwargs.get("instance")
        if settings.DEBUG and instance and instance.email:
            initial.update({"email_confirm": instance.email})

        kwargs.update(initial=initial)
        super().__init__(*args, **kwargs)
        radio_and_select_fields = ["declara_veracidade"]
        for field in self.fields:
            if field not in radio_and_select_fields:
                self.fields[field].widget.attrs["class"] = "form-control"

        self.fields["telefone"].required = True
        self.fields["sexo"].required = True
        self.fields["cpf"].widget.attrs["readonly"] = True
        self.fields["tipo_zona_residencial"].required = True
        self.fields["user"].widget = forms.HiddenInput()

    def save(self, *args, **kwargs):
        if self.instance and is_maior_idade(self.instance.nascimento):
            self.instance.nome_responsavel = self.instance.nome
            self.instance.parentesco_responsavel = choices.GrauParentesco.OUTROS.name
            self.instance.email_responsavel = self.instance.email
        return super().save(*args, **kwargs)

    def clean_declara_veracidade(self):
        valor = self.cleaned_data.get("declara_veracidade", None)
        if not valor:
            raise ValidationError(
                "Você deve marcar este campo para indicar que declara como verídicos os dados apresentados."
            )
        return valor

    def clean_nascimento(self):
        nascimento = self.data["nascimento"]

        if len(nascimento) < 10:  # 'dd/mm/yyyy' == 10
            raise ValidationError("Formato de data inválido.")
        return self.cleaned_data["nascimento"]

    def clean(self):
        data = super().clean()
        nome_responsavel = data.get("nome_responsavel")
        parentesco_responsavel = data.get("parentesco_responsavel")
        nascimento = data.get("nascimento")
        if not is_maior_idade(nascimento):
            if not nome_responsavel:
                self.add_error(
                    "nome_responsavel",
                    "Informe o nome de um responsável pelo candidato menor de idade.",
                )
            if not parentesco_responsavel:
                self.add_error(
                    "parentesco_responsavel",
                    "Informe o grau de parentesco do responsável pelo candidato menor de idade.",
                )
        return data


class CandidatoPreMatriculaForm(DadosBasicosForm):
    class Meta(DadosBasicosForm.Meta):
        model = base_models.PessoaFisica
        exclude = (
            "nome_social",
            "nacionalidade_old",
            "profissao",
            "nome_mae",
            "nome_pai",
        )

        fieldsets = (
            (
                "dados_gerais",
                {
                    "legend": "Informações Básicas",
                    "fields": (
                        "user",
                        "nome",
                        "cpf",
                        "nascimento",
                        "sexo",
                        "tipo_sanguineo",
                        "nacionalidade",
                        "naturalidade",
                        "naturalidade_uf",
                        "nome_responsavel",
                        "parentesco_responsavel",
                        "email_responsavel",
                    ),
                },
            ),
            (
                "rg",
                {
                    "legend": "RG",
                    "fields": (
                        "rg",
                        "orgao_expeditor",
                        "orgao_expeditor_uf",
                        "data_expedicao",
                    ),
                },
            ),
            (
                "certidao",
                {
                    "legend": "Certidão Civil",
                    "fields": (
                        "certidao_tipo",
                        "certidao",
                        "certidao_folha",
                        "certidao_livro",
                        "certidao_data",
                    ),
                },
            ),
            (
                "titulo_eleitor",
                {
                    "legend": "Título de Eleitor",
                    "description": "Somente para maiores de 16 anos.",
                    "fields": (
                        "numero_titulo_eleitor",
                        "zona_titulo_eleitor",
                        "secao_titulo_eleitor",
                        "data_emissao_titulo_eleitor",
                        "uf_titulo_eleitor",
                    ),
                },
            ),
            (
                "endereco",
                {
                    "legend": "Endereço",
                    "fields": (
                        "logradouro",
                        "numero_endereco",
                        "complemento_endereco",
                        "bairro",
                        "municipio",
                        "uf",
                        "cep",
                        "tipo_zona_residencial",
                    ),
                },
            ),
            (
                "contatos",
                {
                    "legend": "Informações para Contatos",
                    "fields": ("telefone", "telefone2", "email", "email_confirm"),
                },
            ),
        )

        row_attrs = {
            "nome": {"class": "form-group col-md-8"},
            "cpf": {"class": "form-group col-md-4 mask-cpf"},
            "nascimento": {
                "class": "form-group has-feedback col-md-4 new-row mask-data"
            },
            "sexo": {"class": "form-group col-md-4"},
            "tipo_sanguineo": {"class": "form-group col-md-4"},
            "nacionalidade": {"class": "form-group col-md-4 new-row"},
            "naturalidade": {"class": "form-group col-md-4"},
            "naturalidade_uf": {"class": "form-group col-md-4"},
            "nome_responsavel": {"class": "form-group col-md-8 new-row"},
            "parentesco_responsavel": {"class": "form-group col-md-4"},
            "email_responsavel": {"class": "form-group col-md-6 new-row"},
            "rg": {"class": "form-group col-md-6 new-row"},
            "orgao_expeditor": {"class": "form-group col-md-6"},
            "orgao_expeditor_uf": {"class": "form-group col-md-6 new-row"},
            "data_expedicao": {"class": "form-group col-md-6 mask-data"},
            "certidao_tipo": {"class": "form-group col-md-6 new-row"},
            "certidao": {"class": "form-group col-md-6"},
            "certidao_folha": {"class": "form-group col-md-4 new-row"},
            "certidao_livro": {"class": "form-group col-md-4"},
            "certidao_data": {"class": "form-group col-md-4 mask-data"},
            "numero_titulo_eleitor": {
                "class": "form-group col-md-8 new-row mask-numero_titulo_eleitor"
            },
            "zona_titulo_eleitor": {"class": "form-group col-md-4"},
            "secao_titulo_eleitor": {"class": "form-group col-md-4 new-row"},
            "data_emissao_titulo_eleitor": {"class": "form-group col-md-4 mask-data"},
            "uf_titulo_eleitor": {"class": "form-group col-md-4"},
            "logradouro": {"class": "form-group col-md-10 new-row"},
            "numero_endereco": {"class": "form-group col-md-2"},
            "complemento_endereco": {"class": "form-group col-md-4 new-row"},
            "bairro": {"class": "form-group col-md-4"},
            "municipio": {"class": "form-group col-md-4"},
            "uf": {"class": "form-group col-md-4 new-row"},
            "cep": {"class": "form-group col-md-4 mask-cep"},
            "tipo_zona_residencial": {"class": "form-group col-md-4"},
            "telefone": {"class": "form-group col-md-6 new-row mask-telefone"},
            "telefone2": {"class": "form-group col-md-6 mask-telefone"},
            "email": {"class": "form-group col-md-6 new-row disablecopypaste"},
            "email_confirm": {"class": "form-group col-md-6 disablecopypaste"},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sexo"].required = True
        self.fields["tipo_sanguineo"].required = True
        self.fields["data_expedicao"].help_text = "Formato DD/MM/AAAA. Ex.: 25/12/1995"
        self.fields["certidao"].required = True
        self.fields["certidao_tipo"].required = True
        self.fields["certidao_folha"].required = True
        self.fields["certidao_livro"].required = True
        self.fields["certidao_data"].required = True
        self.fields["certidao_data"].help_text = "Formato DD/MM/AAAA. Ex.: 25/12/1995"
        self.fields[
            "data_emissao_titulo_eleitor"
        ].help_text = "Formato DD/MM/AAAA. Ex.: 25/12/1995"
        self.fields["telefone"].label = "Telefone Celular"
        self.fields["telefone"].help_text = "Ex.: 83 99999 0000"
        self.fields["telefone2"].help_text = "Ex.: 83 3601 0000"

    def clean_numero_titulo_eleitor(self):
        numero = self.cleaned_data.get("numero_titulo_eleitor")
        if numero:
            return TituloEleitor(numero).numero
        return numero

    def _exige_todos_campos_grupo(self, cleaned_data, fields=None):
        if not fields:
            fields = []
        algum = any([cleaned_data.get(f) for f in fields])
        todos = all([cleaned_data.get(f) for f in fields])
        if algum and not todos:
            for field in [f for f in fields if not cleaned_data.get(f)]:
                if not self.has_error(field):
                    self.add_error(field, "Este campo também deve ser preenchido.")

    def clean(self):
        cleaned_data = super(DadosBasicosForm, self).clean()
        nacimento = cleaned_data.get("nascimento")

        fields_rg = ["rg", "orgao_expeditor", "orgao_expeditor_uf", "data_expedicao"]
        self._exige_todos_campos_grupo(cleaned_data, fields_rg)

        fields_titulo = [
            "numero_titulo_eleitor",
            "uf_titulo_eleitor",
            "secao_titulo_eleitor",
            "zona_titulo_eleitor",
            "data_emissao_titulo_eleitor",
        ]
        if not is_maior_idade(nacimento):
            self._exige_todos_campos_grupo(cleaned_data, fields_titulo)

        return cleaned_data


class CaracterizacaoForm(forms_utils.BetterModelForm):
    nome_pai = forms.CharField(max_length=100, label="Nome do Pai", required=True)
    pai_falecido = forms.ChoiceField(
        choices=choices.SIM_NAO, required=True, widget=forms.RadioSelect
    )
    nome_mae = forms.CharField(max_length=100, label="Nome da Mãe", required=True)
    mae_falecida = forms.ChoiceField(
        choices=choices.SIM_NAO,
        required=True,
        label="Mãe falecida",
        widget=forms.RadioSelect,
    )
    possui_necessidade_especial = forms.ChoiceField(
        choices=choices.SIM_NAO, required=True, widget=forms.RadioSelect
    )
    aluno_exclusivo_rede_publica = forms.ChoiceField(
        choices=choices.SIM_NAO,
        required=True,
        label="Aluno da rede pública",
        widget=forms.RadioSelect,
    )

    class Meta:
        model = models.Caracterizacao
        exclude = (
            "qtd_filhos",
            "ficou_tempo_sem_estudar",
            "tempo_sem_estudar",
            "razao_ausencia_educacional",
            "possui_conhecimento_idiomas",
            "idiomas_conhecidos",
            "possui_conhecimento_informatica",
            "trabalho_situacao",
            "meio_transporte_utilizado",
            "contribuintes_renda_familiar",
            "responsavel_financeiro",
            "responsavel_financeir_trabalho_situacao",
            "responsavel_financeiro_nivel_escolaridade",
            "pai_nivel_escolaridade",
            "mae_nivel_escolaridade",
            "tipo_imovel_residencial",
            "tipo_area_residencial",
            "beneficiario_programa_social",
            "tipo_servico_saude",
            "frequencia_acesso_internet",
            "local_acesso_internet",
            "quantidade_computadores",
            "quantidade_notebooks",
            "quantidade_netbooks",
            "quantidade_smartphones",
        )
        labels = {
            "necessidade_especial": "Especifique as deficiências/necessidades educacionais "
            "especiais"
        }
        help_texts = {
            "necessidade_especial": "Informe as deficiências/necessidades educacionais especiais"
            ' caso você tenha marcado "Sim" na opção anterior.'
        }
        widgets = {
            "necessidade_especial": forms.CheckboxSelectMultiple,
            "candidato": forms.HiddenInput,
        }
        fieldsets = (
            (
                "dados_pessoais",
                {
                    "legend": "Dados Pessoais",
                    "fields": (
                        "candidato",
                        "raca",
                        "estado_civil",
                        "possui_necessidade_especial",
                        "necessidade_especial",
                    ),
                },
            ),
            (
                "dados_familiares",
                {
                    "legend": "Dados Familiares",
                    "fields": (
                        "renda_bruta_familiar",
                        "companhia_domiciliar",
                        "qtd_pessoas_domicilio",
                        "nome_pai",
                        "estado_civil_pai",
                        "pai_falecido",
                        "nome_mae",
                        "estado_civil_mae",
                        "mae_falecida",
                    ),
                },
            ),
            (
                "dados_educacionais",
                {
                    "legend": "Dados Educacionais",
                    "fields": (
                        "escolaridade",
                        "aluno_exclusivo_rede_publica",
                        "escola_ensino_fundamental",
                        "tipo_area_escola_ensino_fundamental",
                        "ensino_fundamental_conclusao",
                        "nome_escola_ensino_fundamental",
                        "municipio_escola_ensino_fundamental",
                        "estado_escola_ensino_fundamental",
                        "escola_ensino_medio",
                        "tipo_area_escola_ensino_medio",
                        "ensino_medio_conclusao",
                        "nome_escola_ensino_medio",
                        "municipio_escola_ensino_medio",
                        "estado_escola_ensino_medio",
                    ),
                },
            ),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        radio_and_select_fields = [
            "necessidade_especial",
            "pai_falecido",
            "mae_falecida",
            "aluno_exclusivo_rede_publica",
            "possui_necessidade_especial",
            "declara_veracidade",
        ]
        for field in self.fields:
            if field not in radio_and_select_fields:
                self.fields[field].widget.attrs["class"] = "form-control"
        self.fields["declara_veracidade"].required = True

    def clean_necessidade_especial(self):
        possui_necessidade_especial = self.cleaned_data.get(
            "possui_necessidade_especial", None
        )
        possui_necessidade_especial = (
            True if possui_necessidade_especial == "True" else False
        )
        necessidade_especial = self.cleaned_data.get("necessidade_especial", None)
        if possui_necessidade_especial and not necessidade_especial.exists():
            raise ValidationError(
                "Você marcou que possui necessidade especial. Portanto, deveria "
                "selecionar o(s) tipo(s) de necessidade(s) especial(is)."
            )
        if not possui_necessidade_especial and necessidade_especial.exists():
            raise ValidationError(
                "Não deveria ter itens selecionados, caso você não possua "
                "necessidade especial."
            )
        return necessidade_especial

    def clean_nome_pai(self):
        nome_pai = self.cleaned_data.get("nome_pai")
        if nome_pai:
            nome_pai = nome_pai.upper()
            self._valida_nome(nome_pai)
        return nome_pai

    def clean_nome_mae(self):
        nome_mae = self.cleaned_data.get("nome_mae")
        if nome_mae:
            nome_mae = nome_mae.upper()
            self._valida_nome(nome_mae)
        return nome_mae

    def _valida_nome(self, nome):
        nomes = nome.split()
        if len(nomes) == 1:
            raise ValidationError(
                "Você deve fornecer nome e sobrenomes separados por espaços em branco."
            )
        for n in nomes:
            if len(n) > 30:
                raise ValidationError(
                    "Você deve fornecer nome e sobrenomes separados por espaços em branco."
                )
            if not n.isalpha():
                raise ValidationError(
                    "Você deve fornecer nome e sobrenomes contendo apenas letras."
                )

    def clean_nome_escola_ensino_fundamental(self):
        nome_escola_ensino_fundamental = self.cleaned_data.get(
            "nome_escola_ensino_fundamental"
        )
        if nome_escola_ensino_fundamental:
            nome_escola_ensino_fundamental = nome_escola_ensino_fundamental.upper()
        return nome_escola_ensino_fundamental

    def clean_nome_escola_ensino_medio(self):
        nome_escola_ensino_medio = self.cleaned_data.get("nome_escola_ensino_medio")
        if nome_escola_ensino_medio:
            nome_escola_ensino_medio = nome_escola_ensino_medio.upper()
        return nome_escola_ensino_medio

    def save(self):
        instance = super().save()
        instance.candidato.nome_mae = self.cleaned_data.get("nome_mae")
        instance.candidato.nome_pai = self.cleaned_data.get("nome_pai")
        instance.candidato.save()
