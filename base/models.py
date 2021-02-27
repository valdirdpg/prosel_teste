import re
from datetime import datetime

import reversion
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from base.utils import is_maior_idade
from . import choices, configs, utils, validators


@reversion.register()
class PessoaFisica(models.Model):
    user = models.OneToOneField(
        User, null=True, blank=True, related_name="pessoa", on_delete=models.SET_NULL
    )
    cpf = models.CharField(
        max_length=14,
        verbose_name="CPF",
        validators=[validators.cpf_validator],
        unique=True,
    )
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome",
        validators=[validators.nome_de_pessoa_validator],
    )
    nome_social = models.CharField(
        max_length=50, verbose_name="Nome Social", null=True, blank=True
    )
    nascimento = models.DateTimeField(verbose_name="Data de Nascimento")
    sexo = models.CharField(
        verbose_name="Sexo",
        choices=choices.Sexo.choices(),
        max_length=1,
        null=True,
        blank=True,
    )
    tipo_sanguineo = models.CharField(
        verbose_name="Tipo Sanguíneo",
        choices=choices.TipoSanguineo.choices(),
        max_length=10,
        null=True,
        blank=True,
    )
    nacionalidade = models.CharField(
        verbose_name="Nacionalidade",
        max_length=55,
        choices=choices.Nacionalidade.choices(),
    )
    nacionalidade_old = models.CharField(
        verbose_name="Nacionalidade (Antigo)", max_length=55, blank=True
    )
    naturalidade = models.CharField(
        verbose_name="Naturalidade", max_length=55, null=True, blank=True
    )
    naturalidade_uf = models.CharField(
        verbose_name="UF da Naturalidade",
        choices=choices.Estados.choices(),
        max_length=2,
        null=True,
        blank=True,
    )
    profissao = models.CharField(
        verbose_name="Profissão/Ocupação", max_length=100, null=True, blank=True
    )
    # Dados Familiares
    nome_mae = models.CharField(
        max_length=100, verbose_name="Nome da Mãe", null=True, blank=True
    )
    nome_pai = models.CharField(
        max_length=100, verbose_name="Nome do Pai", null=True, blank=True
    )
    nome_responsavel = models.CharField(
        verbose_name="Nome do Responsável",
        max_length=100,
        null=True,
        blank=True,
        validators=[validators.nome_de_pessoa_validator],
    )
    email_responsavel = models.EmailField(
        verbose_name="E-mail do Responsável", max_length=100, null=True, blank=True
    )
    parentesco_responsavel = models.CharField(
        verbose_name="Parentesco do Responsável",
        choices=choices.GrauParentesco.choices(),
        max_length=10,
        null=True,
        blank=True,
    )
    # Endereço
    logradouro = models.CharField(max_length=255, verbose_name="Logradouro")
    numero_endereco = models.CharField(max_length=10, verbose_name="Número")
    complemento_endereco = models.CharField(
        verbose_name="Complemento", max_length=255, null=True, blank=True
    )
    uf = models.CharField(
        max_length=2, verbose_name="UF", choices=choices.Estados.choices()
    )
    municipio = models.CharField(max_length=100, verbose_name="Município")
    bairro = models.CharField(max_length=100, verbose_name="Bairro")
    cep = models.CharField(
        max_length=10, verbose_name="CEP", validators=[validators.cep_validator]
    )
    tipo_zona_residencial = models.CharField(
        verbose_name="Zona Residencial",
        choices=choices.TipoZonaResidencial.choices(),
        max_length=15,
        null=True,
        blank=True,
    )
    # Contatos
    telefone = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name="Celular",
        validators=[validators.telefone_validator],
    )
    telefone2 = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name="Telefone Fixo",
        validators=[validators.telefone_validator],
    )
    email = models.EmailField(max_length=55, verbose_name="E-mail")
    # RG
    rg = models.CharField(
        verbose_name="Número do RG", max_length=50, null=True, blank=True
    )
    orgao_expeditor = models.CharField(
        verbose_name="Orgão Emissor do RG", max_length=50, null=True, blank=True
    )
    orgao_expeditor_uf = models.CharField(
        verbose_name="Estado Emissor do RG",
        choices=choices.Estados.choices(),
        max_length=2,
        null=True,
        blank=True,
    )
    data_expedicao = models.DateField(
        verbose_name="Data de Emissão do RG", null=True, blank=True
    )
    # Certidão Civil
    certidao = models.CharField(
        verbose_name="Número do Termo da Certidão Civil",
        max_length=30,
        null=True,
        blank=True,
    )
    certidao_tipo = models.CharField(
        verbose_name="Tipo de Certidão Civil",
        choices=choices.CertidaoCivil.choices(),
        max_length=10,
        null=True,
        blank=True,
    )
    certidao_folha = models.CharField(
        verbose_name="Folha da Certidão Civil", max_length=30, null=True, blank=True
    )
    certidao_livro = models.CharField(
        verbose_name="Livro da Certidão Civil", max_length=30, null=True, blank=True
    )
    certidao_data = models.DateField(
        verbose_name="Data de Emissão da Certidão Civil", null=True, blank=True
    )
    # Título de Eleitor
    numero_titulo_eleitor = models.CharField(
        verbose_name="Número do Título de Eleitor", max_length=30, null=True, blank=True
    )
    zona_titulo_eleitor = models.CharField(
        verbose_name="Zona do Título de Eleitor", max_length=10, null=True, blank=True
    )
    secao_titulo_eleitor = models.CharField(
        verbose_name="Seção do Título de Eleitor", max_length=10, null=True, blank=True
    )
    data_emissao_titulo_eleitor = models.DateField(
        verbose_name="Data de Emissão do Título de Eleitor", null=True, blank=True
    )
    uf_titulo_eleitor = models.CharField(
        verbose_name="Estado Emissor do Título de Eleitor",
        choices=choices.Estados.choices(),
        max_length=10,
        null=True,
        blank=True,
    )

    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Pessoa Física"
        verbose_name_plural = "Pessoas Físicas"

    def __str__(self):
        return f"{self.nome.upper()} (CPF: {self.cpf})"

    @property
    def endereco_completo(self):
        if self.complemento_endereco:
            return "{}, {} - {} - {}, {}/{}".format(
                self.logradouro,
                self.numero_endereco,
                self.complemento_endereco,
                self.bairro,
                self.municipio,
                self.uf,
            )
        return f"{self.logradouro}, {self.numero_endereco} - {self.bairro}, {self.municipio}/{self.uf}"

    def is_atualizado_recentemente(self):
        dias = utils.dias_entre(self.atualizado_em, datetime.now())
        return dias < configs.PortalConfig.DIAS_ATUALIZACAO_DADOS

    def has_dados_suap_completos(self):
        return (
            self._has_certidao_civil()
            and self._has_contatos()
            and self.is_atualizado_recentemente()
        )

    def _has_rg(self):
        return (
            self.rg
            and self.orgao_expeditor
            and self.orgao_expeditor_uf
            and self.data_expedicao
        )

    def _has_certidao_civil(self):
        return (
            self.certidao
            and self.certidao_data
            and self.certidao_folha
            and self.certidao_livro
            and self.certidao_tipo
        )

    def _has_contatos(self):
        return self.telefone and self.email

    @property
    def rg_completo(self):
        if self.rg:
            return (
                f"{self.rg} - {self.orgao_expeditor}/{self.orgao_expeditor_uf} - "
                f'{self.data_expedicao.strftime("%d/%m/%Y")}'
            )
        return "Não Informado"

    @property
    def titulo_eleitor(self):
        if self.numero_titulo_eleitor:
            return (
                f"{self.numero_titulo_eleitor}, Zona {self.zona_titulo_eleitor}, "
                f"Seção {self.secao_titulo_eleitor}"
            )
        return "Não Informado"

    @property
    def naturalidade_completa(self):
        if self.naturalidade_uf:
            return f"{self.naturalidade}/{self.naturalidade_uf}".upper()
        return f"{self.naturalidade}".upper()

    def validate_naturalidade(self):
        erros = dict()
        naturalidade = self.naturalidade
        nacionalidade = self.nacionalidade
        if nacionalidade and nacionalidade == "BRASILEIRA" and not naturalidade:
            erros[
                "naturalidade"
            ] = "Este campo deve ser preenchido para pessoas de nacionalidade Brasileira."
        """if nacionalidade and nacionalidade == "ESTRANGEIRA" and naturalidade:
            erros[
                "naturalidade"
            ] = "Este campo não deve ser preenchido para pessoas de nacionalidade Estrangeira." """
        return erros

    def validate_naturalidade_uf(self):
        erros = dict()
        naturalidade_uf = self.naturalidade_uf
        nacionalidade = self.nacionalidade
        if nacionalidade and nacionalidade == "BRASILEIRA" and not naturalidade_uf:
            erros[
                "naturalidade_uf"
            ] = "Este campo deve ser preenchido para pessoas de nacionalidade Brasileira."
        """if nacionalidade and nacionalidade == "ESTRANGEIRA" and naturalidade_uf:
            erros[
                "naturalidade_uf"
            ] = "Este campo não deve ser preenchido para pessoas de nacionalidade Estrangeira."""
        return erros

    def validate_titulo_eleitor(self):
        erros = dict()
        campos = [
            "numero_titulo_eleitor",
            "zona_titulo_eleitor",
            "secao_titulo_eleitor",
        ]
        for campo in campos:
            valor = getattr(self, campo)
            valor = "" if valor is None else valor
            if not valor and is_maior_idade(self.nascimento):
                maior = configs.PortalConfig.MAIORIDADE
                erros[campo] = f"Obrigatório para maiores de {maior} anos."
            elif valor and not re.sub(r"[-\.\/\s]", "", valor).isdigit():
                erros[campo] = "Deve conter apenas números."
        return erros

    def clean(self):
        super().clean()
        erros = dict()
        erros.update(self.validate_naturalidade())
        erros.update(self.validate_naturalidade_uf())
        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.user_id:
            if self.email and self.email != self.user.email:
                self.user.email = self.email
            if self.nome:
                self.user.first_name, *ignore, self.user.last_name = self.nome.split()
            self.user.save()
