from datetime import datetime

from ckeditor.fields import RichTextField
from django.core.exceptions import ValidationError
from django.db import models

from base import choices, models as base_models
from base.configs import PortalConfig as Config
from base.utils import dias_entre


class NecessidadeEspecial(models.Model):
    descricao = models.CharField("Descrição", max_length=50)

    class Meta:
        verbose_name = "Necessidade Especial"
        verbose_name_plural = "Necessidades Especiais"

    def __str__(self):
        return self.descricao


class Idioma(models.Model):
    descricao = models.CharField("Idioma", max_length=50)
    uso_caracterizacao = models.BooleanField("Usar na caracterização", default=True)

    class Meta:
        verbose_name = "Idioma"
        verbose_name_plural = "Idiomas"

    def __str__(self):
        return self.descricao


class SituacaoTrabalho(models.Model):
    descricao = models.CharField(max_length=50, verbose_name="Descrição")

    class Meta:
        verbose_name = "Situação de Trabalho"
        verbose_name_plural = "Situações de Trabalho"

    def __str__(self):
        return self.descricao


class MeioTransporte(models.Model):
    descricao = models.CharField(max_length=50, verbose_name="Meio de Transporte")

    class Meta:
        verbose_name = "Meio de Transporte"
        verbose_name_plural = "Meios de Transporte"

    def __str__(self):
        return self.descricao


class Raca(models.Model):
    descricao = models.CharField("Descrição", max_length=50, unique=True)
    valor_suap = models.CharField(
        verbose_name="Valor utilizado no Suap", max_length=50, blank=True
    )

    class Meta:
        verbose_name = "Etnia"
        verbose_name_plural = "Etnias"

    def __str__(self):
        return self.descricao


class ContribuinteRendaFamiliar(models.Model):
    descricao = models.CharField(max_length=50, verbose_name="Descrição")

    class Meta:
        verbose_name = "Contribuinte de Renda Familiar"
        verbose_name_plural = "Contribuintes de Renda Familiar"

    def __str__(self):
        return self.descricao


class CompanhiaDomiciliar(models.Model):
    descricao = models.CharField(max_length=50, verbose_name="Descrição")

    class Meta:
        verbose_name = "Companhia Domiciliar"
        verbose_name_plural = "Companhias Domiciliares"

    def __str__(self):
        return self.descricao


class TipoImovelResidencial(models.Model):
    descricao = models.CharField(max_length=50, verbose_name="Descrição")

    class Meta:
        verbose_name = "Tipo de Imóvel Residencial"
        verbose_name_plural = "Tipos de Imóveis Residenciais"

    def __str__(self):
        return self.descricao


class TipoEscola(models.Model):
    descricao = models.CharField("Descrição", max_length=50)
    valor_suap = models.CharField(
        verbose_name="Valor utilizado no Suap", max_length=50, blank=True
    )

    class Meta:
        verbose_name = "Tipo de Escola"
        verbose_name_plural = "Tipos de Escolas"

    def __str__(self):
        return self.descricao


class TipoAreaResidencial(models.Model):
    descricao = models.CharField(max_length=50, verbose_name="Descrição")

    class Meta:
        verbose_name = "Tipo de Área Residencial"
        verbose_name_plural = "Tipos de Áreas Residenciais"

    def __str__(self):
        return self.descricao


class TipoServicoSaude(models.Model):
    descricao = models.CharField("Descrição", max_length=50)

    def __str__(self):
        return self.descricao


class BeneficioGovernoFederal(models.Model):
    descricao = models.CharField(max_length=100, verbose_name="Descrição")

    class Meta:
        verbose_name = "Benefício do Governo Federal"
        verbose_name_plural = "Benefícios de Governo Federal"

    def __str__(self):
        return self.descricao


class TipoEmprego(models.Model):
    descricao = models.CharField(max_length=50, verbose_name="Descrição")

    class Meta:
        verbose_name = "Tipo de Emprego"
        verbose_name_plural = "Tipos de Emprego"

    def __str__(self):
        return self.descricao


class TipoAcessoInternet(models.Model):
    descricao = models.CharField("Descrição", max_length=50)

    def __str__(self):
        return self.descricao


class RazaoAfastamentoEducacional(models.Model):
    descricao = models.CharField(verbose_name="Descrição", max_length=50)

    class Meta:
        verbose_name = "Razão de Afastamento Educacional"
        verbose_name_plural = "Razões de Afastamentos Educacionais"

    def __str__(self):
        return self.descricao


class EstadoCivil(models.Model):
    descricao = models.CharField(verbose_name="Descrição", max_length=50)
    valor_suap = models.CharField(
        verbose_name="Valor utilizado no Suap", max_length=50, blank=True
    )

    class Meta:
        verbose_name = "Estado Civil"
        verbose_name_plural = "Estados Civis"

    def __str__(self):
        return self.descricao


class ComunicadoCandidato(models.Model):
    CONVOCACAO = "Convocação"
    RES_PARCIAL_MAT = "Resultado parcial de mátricula"

    CHOICES = ((CONVOCACAO, CONVOCACAO), (RES_PARCIAL_MAT, RES_PARCIAL_MAT))

    tipo = models.CharField(choices=CHOICES, max_length=50)
    assunto = models.CharField(verbose_name="Assunto", max_length=50)
    mensagem = RichTextField()

    class Meta:
        verbose_name = "Comunicado ao Candidato"
        verbose_name_plural = "Comunicados aos Candidatos"

    def __str__(self):
        return self.tipo


class NivelEscolaridade(models.Model):
    descricao = models.CharField(verbose_name="Descrição", max_length=50)

    class Meta:
        verbose_name = "Nível de Escolaridade"
        verbose_name_plural = "Níveis de Escolaridade"

    def __str__(self):
        return self.descricao


class RendimentoCaracterizacao(models.Model):
    MESADA = "Mesada"
    AUX_PARENTES = "Auxílio de parentes ou amigos"
    ALUGUEL = "Aluguel/Arrendamento"
    OUTROS = "Outros"

    CHOICES = (
        (MESADA, MESADA),
        (AUX_PARENTES, AUX_PARENTES),
        (ALUGUEL, ALUGUEL),
        (OUTROS, OUTROS),
    )

    tipo = models.CharField(choices=CHOICES, max_length=50)
    outro_tipo = models.CharField(blank=True, max_length=50)


class Candidato(base_models.PessoaFisica):
    class Meta:
        proxy = True
        ordering = ["nome"]


class Caracterizacao(models.Model):
    """
    Dados Socioeconômicos
    É a caracterização feita pelo aluno, mas o setor AE pode mudar algumas
    informações.
    """

    # Dados pessoais
    candidato = models.ForeignKey(
        base_models.PessoaFisica, verbose_name="Candidato", on_delete=models.CASCADE
    )
    raca = models.ForeignKey(
        Raca,
        verbose_name="Etnia/Raça/Cor",
        default=0,
        on_delete=models.CASCADE,
        help_text="Como você se considera quanto a sua questão racial?",
    )
    possui_necessidade_especial = models.BooleanField(
        verbose_name="Você é uma pessoa com deficiência / necessidade educacional especial?"
    )
    necessidade_especial = models.ManyToManyField(
        NecessidadeEspecial,
        verbose_name="Necessidades educacionais especiais",
        blank=True,
    )
    estado_civil = models.ForeignKey(
        EstadoCivil,
        related_name="alunos",
        verbose_name="Estado Civil",
        default=0,
        on_delete=models.CASCADE,
    )
    qtd_filhos = models.PositiveIntegerField(
        default=0, verbose_name="Quantidade de filhos", blank=True
    )

    # Dados educacionais
    escolaridade = models.ForeignKey(
        NivelEscolaridade,
        verbose_name="Nivel de escolaridade",
        related_name="candidato",
        on_delete=models.CASCADE,
    )
    aluno_exclusivo_rede_publica = models.BooleanField(
        verbose_name="Aluno da rede pública",
        help_text="Marque caso possua histórico escolar integral a partir do 6° ano do Ensino Fundamental até o 3° ano do Ensino Médio exclusivamente em escola da rede pública do país.",
    )
    ensino_fundamental_conclusao = models.PositiveIntegerField(
        verbose_name="Ano de conclusão do Ensino Fundamental"
    )
    ensino_medio_conclusao = models.PositiveIntegerField(
        verbose_name="Ano de conclusão do Ensino Médio", blank=True, null=True
    )
    ficou_tempo_sem_estudar = models.BooleanField(
        verbose_name="Ausência escolar",
        blank=True,
        default=False,
        help_text="Marque caso tenha permanecido algum tempo sem estudar.",
    )
    tempo_sem_estudar = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Período de Ausência",
        help_text="Informe quantos anos ficou sem estudar caso tenha marcado a opção anterior.",
    )
    razao_ausencia_educacional = models.ForeignKey(
        RazaoAfastamentoEducacional,
        null=True,
        blank=True,
        verbose_name="Motivo da Ausência Escolar",
        on_delete=models.SET_NULL,
        help_text="Informe o motivo pelo qual você ficou sem estudar caso tenha marcado a opção anterior.",
    )
    possui_conhecimento_idiomas = models.BooleanField(
        verbose_name="Conhecimento em idiomas", default=False
    )
    idiomas_conhecidos = models.ManyToManyField(
        Idioma,
        verbose_name="Idiomas",
        blank=True,
        help_text="Informe os idiomas sobre os quais você tem conhecimento caso tenha marcado a opção anterior.",
    )
    possui_conhecimento_informatica = models.BooleanField(
        verbose_name="Conhecimento em informática", default=False, blank=True
    )
    escola_ensino_fundamental = models.ForeignKey(
        TipoEscola,
        on_delete=models.CASCADE,
        related_name="escola_ensino_fundamental",
        verbose_name="Tipo de escola do Ensino Fundamental",
        help_text="Informe o tipo de escola que você cursou durante o Ensino Fundamental.",
    )
    nome_escola_ensino_fundamental = models.CharField(
        verbose_name="Nome da escola do Ensino Fundamental",
        max_length=50,
        help_text="Informe o nome da escola que você cursou durante o Ensino Fundamental.",
    )
    tipo_area_escola_ensino_fundamental = models.ForeignKey(
        TipoAreaResidencial,
        on_delete=models.CASCADE,
        verbose_name="Localização da escola do Ensino Fundamental",
        help_text="Informe a localização da escola que você cursou durante o Ensino Fundamental.",
        related_name="tipo_area_escola_ensino_fundamental",
    )
    municipio_escola_ensino_fundamental = models.CharField(
        max_length=50,
        null=True,
        blank="True",
        verbose_name="Município da escola de Ensino Fundamental",
    )
    estado_escola_ensino_fundamental = models.CharField(
        max_length=50,
        null=True,
        blank="True",
        verbose_name="Estado onde está localizada a Escola de Ensino Fundamental",
        choices=choices.Estados.choices(),
    )
    escola_ensino_medio = models.ForeignKey(
        TipoEscola,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Tipo de escola do Ensino Médio",
        related_name="escola_ensino_medio",
        help_text="Informe o tipo de escola que você cursou durante o Ensino Médio.",
    )
    nome_escola_ensino_medio = models.CharField(
        verbose_name="Nome da escola do Ensino Médio",
        max_length=50,
        null=True,
        blank="True",
        help_text="Informe o nome da escola que você cursou durante o Ensino Médio.",
    )
    tipo_area_escola_ensino_medio = models.ForeignKey(
        TipoAreaResidencial,
        on_delete=models.SET_NULL,
        verbose_name="Localização da escola do Ensino Médio",
        help_text="Informe a localização da escola que você curso durante o Ensino Médio",
        blank=True,
        null=True,
        related_name="tipo_area_escola_ensino_medio",
    )
    municipio_escola_ensino_medio = models.CharField(
        max_length=50,
        null=True,
        blank="True",
        verbose_name="Município da escola de Ensino Médio",
    )
    estado_escola_ensino_medio = models.CharField(
        max_length=50,
        null=True,
        blank="True",
        verbose_name="Estado onde está localizada a Escola de Ensino Médio",
        choices=choices.Estados.choices(),
    )

    # Situação familiar e socio-econômica
    trabalho_situacao = models.ForeignKey(
        SituacaoTrabalho,
        verbose_name="Situação de trabalho",
        help_text="Situação em que você se encontra no mercado de trabalho.",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    meio_transporte_utilizado = models.ManyToManyField(
        MeioTransporte,
        verbose_name="Meio de transporte",
        blank=True,
        help_text="Meio de transporte que você utiliza/utilizará para se deslocar.",
    )
    contribuintes_renda_familiar = models.ManyToManyField(
        ContribuinteRendaFamiliar,
        blank=True,
        verbose_name="Contribuintes da renda familiar",
        help_text="Pessoas que contribuem para rendar familiar.",
    )
    responsavel_financeiro = models.ForeignKey(
        ContribuinteRendaFamiliar,
        on_delete=models.CASCADE,
        verbose_name="Principal responsável pela renda familiar",
        help_text="Pessoa responsável pela renda familiar",
        related_name="responsavel_financeiro",
        null=True,
        blank=True,
    )
    responsavel_financeir_trabalho_situacao = models.ForeignKey(
        SituacaoTrabalho,
        related_name="responsavel_financeiro",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Situação de trabalho do principal responsável financeiro",
        help_text="Situação em que seu pai se encontra no mercado de trabalho.",
    )
    responsavel_financeiro_nivel_escolaridade = models.ForeignKey(
        NivelEscolaridade,
        on_delete=models.CASCADE,
        related_name="responsavel_financeiro",
        null=True,
        blank=True,
        verbose_name="Nível de escolaridade do principal responsável financeiro",
    )
    pai_nivel_escolaridade = models.ForeignKey(
        NivelEscolaridade,
        related_name="pai",
        on_delete=models.CASCADE,
        verbose_name="Nível de escolaridade do pai",
        null=True,
        blank=True,
    )
    mae_nivel_escolaridade = models.ForeignKey(
        NivelEscolaridade,
        related_name="mae",
        on_delete=models.CASCADE,
        verbose_name="Nível de escolaridade da mãe",
        null=True,
        blank=True,
    )
    renda_bruta_familiar = models.DecimalField(
        verbose_name="Renda Bruta Familiar R$",
        max_digits=8,
        decimal_places=2,
        help_text="Considerar a soma de todos os rendimentos mensais da família sem os descontos.",
    )
    companhia_domiciliar = models.ForeignKey(
        CompanhiaDomiciliar,
        verbose_name="Companhia domiciliar",
        help_text="Com quem você mora?",
        on_delete=models.CASCADE,
    )
    qtd_pessoas_domicilio = models.PositiveIntegerField(
        verbose_name="Número de pessoas no domicílio",
        help_text="Número de pessoas que moram na sua residência (incluindo você).",
    )
    tipo_imovel_residencial = models.ForeignKey(
        TipoImovelResidencial,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Tipo de imóvel em que reside",
    )
    tipo_area_residencial = models.ForeignKey(
        TipoAreaResidencial,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Tipo de área residencial em que reside",
    )
    beneficiario_programa_social = models.ManyToManyField(
        BeneficioGovernoFederal,
        verbose_name="Programas sociais do Governo Federal",
        blank=True,
        help_text="Informe os programas do governo federal dos quais você ou algum membro de sua família seja beneficiário.",
    )
    tipo_servico_saude = models.ForeignKey(
        TipoServicoSaude,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Serviço de saúde que você mais utiliza",
    )
    pai_falecido = models.BooleanField(verbose_name="Pai falecido")
    mae_falecida = models.BooleanField(verbose_name="Mãe falecida")
    estado_civil_pai = models.ForeignKey(
        EstadoCivil,
        related_name="pais_candidatos",
        verbose_name="Estado Civil do Pai",
        default=11,
        on_delete=models.CASCADE,
    )
    estado_civil_mae = models.ForeignKey(
        EstadoCivil,
        related_name="maes_candidatos",
        verbose_name="Estado Civil da Mãe",
        default=11,
        on_delete=models.CASCADE,
    )

    # Acesso às tecnologias da informação
    frequencia_acesso_internet = models.ForeignKey(
        TipoAcessoInternet,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Frequência de Acesso à Internet",
    )
    local_acesso_internet = models.CharField(
        "Local de acesso à internet", max_length=50, null=True, blank=True
    )
    quantidade_computadores = models.PositiveIntegerField(
        "Quantidade de computadores desktop que possui", null=True, blank=True
    )
    quantidade_notebooks = models.PositiveIntegerField(
        "Quantidade de notebooks que possui", null=True, blank=True
    )
    quantidade_netbooks = models.PositiveIntegerField(
        "Quantidade de netbooks que possui", null=True, blank=True
    )
    quantidade_smartphones = models.PositiveIntegerField(
        "Quantidade de smartphones que possui", null=True, blank=True
    )

    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    declara_veracidade = models.BooleanField(verbose_name=Config.DECLARACAO_VERACIDADE)

    class Meta:
        verbose_name = "Caracterização Social"
        verbose_name_plural = "Caracterizações Sociais"
        ordering = ["candidato__nome"]

    def __str__(self):
        return str(self.candidato)

    @property
    def renda_per_capita(self):
        if self.qtd_pessoas_domicilio > 0:
            return round(self.renda_bruta_familiar / self.qtd_pessoas_domicilio, 2)
        return None

    def is_atualizado_recentemente(self, limite_dias=Config.DIAS_ATUALIZACAO_DADOS):
        dias = dias_entre(self.atualizado_em, datetime.now())
        return dias <= limite_dias

    def validate_declara_veracidade(self):
        erros = dict()
        valor = self.declara_veracidade
        if not valor:
            erros[
                "declara_veracidade"
            ] = "Você deve marcar este campo para indicar que declara como verídicos os dados apresentados."
        return erros

    def validate_tempo_sem_estudar(self):
        erros = dict()
        ficou_sem_estudar = self.ficou_tempo_sem_estudar
        tempo_sem_estudar = self.tempo_sem_estudar
        if ficou_sem_estudar and not tempo_sem_estudar:
            erros[
                "tempo_sem_estudar"
            ] = "Se você ficou algum tempo sem estudar, informe a quantidade anos."
        idade = datetime.now().year - self.candidato.nascimento.year
        if ficou_sem_estudar and tempo_sem_estudar and tempo_sem_estudar > idade:
            erros[
                "tempo_sem_estudar"
            ] = "Este valor é incompatível, pois é maior que a idade do candidato."
        if not ficou_sem_estudar and tempo_sem_estudar and tempo_sem_estudar != 0:
            erros[
                "tempo_sem_estudar"
            ] = "Este campo deveria ter o valor zero, caso você não tenha ficado sem estudar."
        return erros

    def validate_razao_ausencia_educacional(self):
        erros = dict()
        ficou_sem_estudar = self.ficou_tempo_sem_estudar
        razao_ausencia_educacional = self.razao_ausencia_educacional
        if ficou_sem_estudar and not razao_ausencia_educacional:
            erros[
                "razao_ausencia_educacional"
            ] = "Se você ficou algum tempo sem estudar, informe o motivo."
        if not ficou_sem_estudar and razao_ausencia_educacional:
            erros[
                "razao_ausencia_educacional"
            ] = "Se você não ficou tempo sem estudar, este campo deveria estar vazio."
        return erros

    def validate_ensino_fundamental_conclusao(self):
        erros = dict()
        ano_ensino_fundamental = self.ensino_fundamental_conclusao
        ano_ensino_medio = self.ensino_medio_conclusao
        if (
            ano_ensino_fundamental
            and ano_ensino_medio
            and ano_ensino_fundamental > ano_ensino_medio
        ):
            erros[
                "ensino_fundamental_conclusao"
            ] = "Deve ser anterior ou igual ao ano de conclusão do ensino médio."
        idade = datetime.now().year - self.candidato.nascimento.year
        ano_atual = datetime.now().year
        ano_minimo = ano_atual - idade
        if ano_ensino_fundamental not in range(ano_minimo, ano_atual + 1):
            erros[
                "ensino_fundamental_conclusao"
            ] = f"Ano inválido. Por favor, forneça um ano entre {ano_minimo} e {ano_atual}."
        return erros

    def validate_ensino_medio_conclusao(self):
        erros = dict()
        ano_conclusao = self.ensino_medio_conclusao
        idade = datetime.now().year - self.candidato.nascimento.year
        ano_atual = datetime.now().year
        ano_minimo = ano_atual - idade
        if ano_conclusao not in range(ano_minimo, ano_atual + 1):
            erros[
                "ensino_medio_conclusao"
            ] = f"Ano inválido. Por favor, forneça um ano entre {ano_minimo} e {ano_atual}."
        return erros

    def validate_nome_escola_ensino_fundamental(self):
        erros = dict()
        nome = self.nome_escola_ensino_fundamental
        if nome and nome.isdigit():
            erros["nome_escola_ensino_fundamental"] = "Deve conter o nome da escola."
        return erros

    def validate_nome_escola_ensino_medio(self):
        erros = dict()
        nome = self.nome_escola_ensino_medio
        if nome and nome.isdigit():
            erros["nome_escola_ensino_medio"] = "Deve conter o nome da escola."
        return erros

    def clean(self):
        super().clean()
        erros = dict()
        erros.update(self.validate_declara_veracidade())
        erros.update(self.validate_tempo_sem_estudar())
        erros.update(self.validate_razao_ausencia_educacional())
        erros.update(self.validate_ensino_fundamental_conclusao())
        erros.update(self.validate_nome_escola_ensino_fundamental())
        erros.update(self.validate_nome_escola_ensino_medio())
        if erros:
            raise ValidationError(erros)
