import re

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from form_utils import forms as forms_utils
from snowpenguin.django.recaptcha2.widgets import (
    ReCaptchaWidget,
)  # pylint: disable=import-error

from base import choices, utils as base_utils
from base.fields import SafeReCaptchaField
from base.forms import Form
from base.models import PessoaFisica
from base.utils import CPF
from psct.models import candidato as models
from psct.validators import senha_eh_valida


class CandidatoForm(forms_utils.BetterModelForm):
    declara_veracidade = forms.BooleanField(
        label="DECLARO, para os fins de direito, sob as penas da lei, que as informações que apresento para o cadastro, "
        "são fiéis à verdade e condizentes com a realidade dos fatos. Fico ciente, portanto, que a falsidade desta "
        "declaração configura-se em crime previsto no Código Penal Brasileiro e passível de apuração na forma da Lei."
    )
    email_confirm = forms.EmailField(max_length=55, label="Confirma E-mail")

    class Meta:
        model = models.Candidato
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
                    "legend": "Contatos",
                    "fields": ("telefone", "email", "email_confirm"),
                },
            ),
        )

        class Media:
            js = ("js/utils.js", "js/responsaveis.js, js/script.js")
        row_attrs = {
            "cpf": {"class": "mask-cpf"},
            "nascimento": {"class": "has-feedback mask-data"},
            "cep": {"class": "mask-cep"},
            "telefone": {"class": "mask-telefone"},
            "email_confirm": {"class": "disablecopypaste"},
            "password_confirm": {"class": "disablecopypaste"},
        }



    def __init__(self, *args, **kwargs):
        # Obriga o Candidato a sempre clicar no CheckBox quando atualizar os dados
        initial = {"declara_veracidade": False}

        instance = kwargs.get("instance")
        if instance:
            initial["email_confirm"] = instance.email

        kwargs.update(initial=initial)
        super().__init__(*args, **kwargs)
        radio_and_select_fields = ["declara_veracidade"]
        for field in self.fields:
            if field not in radio_and_select_fields:
                self.fields[field].widget.attrs["class"] = "form-control"

        self.fields["naturalidade"].label = "Município de Nascimento"
        self.fields["naturalidade_uf"].label = "Estado de Nascimento"
        self.fields["uf"].label = "Estado"
        self.fields["telefone"].label = "Telefone"
        self.fields["telefone"].required = True

        self.fields["cpf"].help_text = "Utilize somente o CPF do/a estudante candidato/a."
        self.fields[
            "nascimento"
        ].help_text = "Preencher a data no formato DD/MM/AAAA. Ex.: 25/12/1995"
        self.fields["naturalidade"].help_text = "Obrigatório para brasileiros."
        self.fields["naturalidade_uf"].help_text = "Obrigatório para brasileiros."
        self.fields[
            "nome_responsavel"
        ].help_text = "Obrigatório para menores de 18 anos."
        self.fields[
            "parentesco_responsavel"
        ].help_text = "Obrigatório para menores de 18 anos."
        self.fields["logradouro"].help_text = "Ex.: Rua, Avenida, Sítio, etc."
        self.fields["complemento_endereco"].help_text = "Ex.: Casa B, Apto 301, etc."
        self.fields[
            "cep"
        ].help_text = "Preencher o cep no formato NN.NNN-NNN (Ex.: 58.000-300)"
        self.fields["telefone"].help_text = "Ex.: 83 3601 0000, ou 83 99999 0000"

        self.fields["sexo"].required = True
        self.fields["tipo_zona_residencial"].required = True
        self.fields["cpf"].widget.attrs["readonly"] = True

        self.fields["user"].widget = forms.HiddenInput()

    def save(self, *args, **kwargs):
        if self.instance and base_utils.is_maior_idade(self.instance.nascimento):
            self.instance.nome_responsavel = self.instance.nome
            self.instance.parentesco_responsavel = choices.GrauParentesco.OUTROS.name
        result = super().save(*args, **kwargs)
        user = self.instance.user
        if not user.groups.filter(name="Candidatos PSCT").exists():
            group = Group.objects.get(name="Candidatos PSCT")
            user.groups.add(group)
            self.instance.user = user
        return result

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
            raise ValidationError(
                "A data deve ser digitada no formato DD/MM/AAAA. Exemplo: 25/12/1954."
            )
        return self.cleaned_data["nascimento"]

    def clean(self):
        data = super().clean()
        nome_responsavel = data.get("nome_responsavel")
        parentesco_responsavel = data.get("parentesco_responsavel")
        nascimento = data.get("nascimento")
        if not base_utils.is_maior_idade(nascimento):
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
        return self.cleaned_data


class CandidatoReadonlyForm(CandidatoForm):
    class Meta(CandidatoForm.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["nome"].widget.attrs["readonly"] = True
        self.fields["cpf"].widget.attrs["readonly"] = True
        self.fields["nascimento"].widget.attrs["readonly"] = True
        self.fields["nome_responsavel"].widget.attrs["readonly"] = True
        self.fields["parentesco_responsavel"].widget.attrs["readonly"] = True
        self.fields["nacionalidade"].widget.attrs["readonly"] = True
        self.fields["naturalidade"].widget.attrs["readonly"] = True
        self.fields["sexo"].widget.attrs["readonly"] = True
        self.fields["naturalidade_uf"].widget.attrs["readonly"] = True


class CandidatoCadastroForm(CandidatoForm):
    password = forms.CharField(
        max_length=32,
        widget=forms.PasswordInput,
        label="Senha",
        help_text="A senha deve conter letras, números e, no mínimo, 8 caracteres.",
    )
    password_confirm = forms.CharField(
        max_length=32, widget=forms.PasswordInput, label="Confirma Senha"
    )
    if not settings.DEBUG:
        captcha = SafeReCaptchaField(widget=ReCaptchaWidget())

    class Meta(CandidatoForm.Meta):
        fieldsets = CandidatoForm.Meta.fieldsets + (
            (
                "autenticacao",
                {
                    "legend": "Senha",
                    "fields": ("password", "password_confirm", "captcha"),
                },
            ),
        )

    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial")
        super().__init__(*args, **kwargs)
        self.fields["cpf"].initial = initial.get("cpf", "")
        self.fields["cpf"].widget.attrs["readonly"] = False

        self.fields["email_confirm"].help_text = "Digite novamente seu e-mail."
        self.fields["password_confirm"].help_text = "Digite novamente sua senha."

    def clean_password(self):
        senha = self.cleaned_data.get("password", None)
        if senha:
            senha_eh_valida(senha)
        return senha

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            msg = "A senha e a confirmação de senha devem ser iguais."
            self.add_error("password", msg)
            self.add_error("password_confirm", msg)

        email = cleaned_data.get("email")
        email_confirm = cleaned_data.get("email_confirm")

        if email and email_confirm and email != email_confirm:
            msg = "O email e a confirmação devem ser iguais"
            self.add_error("email", msg)
            self.add_error("email_confirm", msg)

        return cleaned_data

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf")
        if cpf and models.Candidato.objects.filter(cpf=cpf).exists():
            raise ValidationError("Já existe um candidato cadastrado com esse CPF.")
        username = re.sub(r"[-\.]", "", cpf)
        if cpf and User.objects.filter(username=username).exists():
            raise ValidationError("Já existe um usuário cadastrado com esse CPF.")
        return cpf

    def save(self):
        cpf = re.sub(r"[-\.]", "", self.instance.cpf)
        user = User.objects.create(
            username=cpf,
            first_name=self.instance.nome.split(" ")[0],
            last_name=self.instance.nome.split(" ")[-1],
            email=self.instance.email,
        )
        if self.cleaned_data and self.cleaned_data["password"]:
            user.set_password(self.cleaned_data["password"])
        user.save()
        self.instance.user = user
        super().save()


class CandidatoAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="CPF",
        max_length=15,
        help_text="Apenas números (não é necessário '.' ou '-')",
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput,
        help_text='<a href="{}" class="pull-right">Perdeu sua senha?</a>'.format(
            "/password_reset/"
        ),
    )
    if not settings.DEBUG:
        captcha = SafeReCaptchaField(widget=ReCaptchaWidget())


class PreCadastroCandidatoForm(forms_utils.BetterForm):
    cpf = forms.CharField(label="CPF", help_text="Utilize somente o CPF do/a estudante candidato/a.")

    class Meta:
        fieldsets = (("", {"fields": ("cpf",)}),)
        row_attrs = {"cpf": {"class": "mask-cpf"}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        radio_and_select_fields = []
        for field in self.fields:
            if field not in radio_and_select_fields:
                self.fields[field].widget.attrs["class"] = "form-control"

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf")
        if cpf:
            if not CPF(cpf).valido():
                raise ValidationError("CPF inválido.")
            if PessoaFisica.objects.filter(cpf=cpf).exists():
                raise ValidationError(
                    "Já existe um candidato cadastrado com o CPF informado"
                )
        return cpf


class ImportarSISUForm(Form):
    cpf = forms.CharField(label="CPF")

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf")
        if cpf:
            if not CPF(cpf).valido():
                raise ValidationError("CPF inválido.")
            if not models.models_base.PessoaFisica.objects.filter(cpf=cpf).exists():
                raise ValidationError(
                    "Não existe nenhum candidato com o CPF informado."
                )
            if models.Candidato.objects.filter(cpf=cpf).exists():
                raise ValidationError("Candidato com o CPF informado já existe.")
        return cpf
