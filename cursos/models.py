from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.text import get_valid_filename, slugify
from suaprest import django as suaprest

import base.choices
from base.history import HistoryMixin
from base.utils import get_src_mapa, normalizar_nome_proprio
from noticias.models import PalavrasChave
from processoseletivo.models import ProcessoSeletivo
from registration import utils
from . import choices
from .validators import validate_file_size, validate_file_type


def generate_atoregulatorio_curso_path(self, filename):
    url = f"cursos/{slugify(self.curso.pk)}/atos_regulatorios/{get_valid_filename(filename)}"
    return url


def generate_plano_disciplina_path(self, filename):
    url = f"cursos/{self.curso.pk}/disciplina/{get_valid_filename(filename)}"
    return url


def generate_documento_curso_path(self, filename):
    url = f"cursos/{slugify(self.curso.pk)}/documentos/{get_valid_filename(filename)}"
    return url


class IES(models.Model):
    codigo = models.IntegerField(verbose_name="Código", unique=True)
    uf = models.CharField(
        verbose_name="UF", choices=base.choices.Estados.choices(), max_length=2
    )
    nome = models.CharField(verbose_name="Nome", max_length=255, unique=True)
    sigla = models.CharField(verbose_name="Sigla", max_length=10, unique=True)
    ci = models.CharField(
        verbose_name="Conceito Institucional", max_length=10, blank=True, null=True
    )
    igc = models.CharField(
        verbose_name="Índice Geral de Cursos", max_length=10, blank=True, null=True
    )

    class Meta:
        verbose_name = "Instituição de Ensino"
        verbose_name_plural = "Instituições de Ensino"

    def __str__(self):
        return self.nome


class Cidade(models.Model):
    nome = models.CharField(max_length=255)
    uf = models.CharField(
        verbose_name="UF", choices=base.choices.Estados.choices(), max_length=2
    )

    def __str__(self):
        return f"{self.nome}/{self.uf}"


class TipoAtoRegulatorio(models.Model):
    nome = models.CharField(max_length=128, unique=True)

    class Meta:
        verbose_name = "Tipo de Ato Regulatório"
        verbose_name_plural = "Tipos de Atos Regulatórios"

    def __str__(self):
        return self.nome


class TipoDocumentoQuerySet(models.QuerySet):
    def obrigatorios_nivel_tecnico(self):
        return self.filter(obrigatorio_tecnico=True)

    def obrigatorios_graduacao(self):
        return self.filter(obrigatorio_graduacao=True)

    def obrigatorios_pos_graduacao(self):
        return self.filter(obrigatorio_pos_graduacao=True)


class TipoDocumento(models.Model):
    nome = models.CharField(max_length=128, unique=True)
    obrigatorio_tecnico = models.BooleanField(
        verbose_name="Obrigatório para curso técnico",
        default=False,
        help_text="""Ao marcar este campo, você exige que o coordenador do curso cadastre
                                                   pelo menos um documento deste tipo para cursos técnicos.""",
    )
    obrigatorio_graduacao = models.BooleanField(
        verbose_name="Obrigatório para curso de graduação",
        default=False,
        help_text="""Ao marcar este campo, você exige que o coordenador do curso cadastre
                                                   pelo menos um documento deste tipo para cursos de graduação.""",
    )
    obrigatorio_pos_graduacao = models.BooleanField(
        verbose_name="Obrigatório para curso de pós-graduação",
        default=False,
        help_text="""Ao marcar este campo, você exige que o coordenador do curso cadastre
                                                   pelo menos um documento deste tipo para cursos de pós-graduação.""",
    )

    objects = TipoDocumentoQuerySet.as_manager()

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class ServidorQuerySet(models.QuerySet):
    def por_tipo(self, tipo):
        return self.filter(tipo=tipo)

    def taes(self):
        return self.por_tipo(base.choices.TipoServidor.TAE.name)

    def docentes(self):
        return self.por_tipo(base.choices.TipoServidor.DOCENTE.name)

    def docentes_externos(self):
        return self.por_tipo(base.choices.TipoServidor.DOCENTE_EXTERNO.name)

    def terceirizados(self):
        return self.por_tipo(base.choices.TipoServidor.TERCEIRIZADO.name)

    def efetivos(self):
        return self.docentes() | self.taes()


class Servidor(models.Model):
    nome = models.CharField(verbose_name="Nome", max_length=255)
    matricula = models.CharField(
        verbose_name="Matrícula",
        max_length=11,
        help_text="Matrícula SIAPE sem dígito verificador.",
        unique=True,
    )
    titulacao = models.CharField(
        verbose_name="Titulação acadêmica",
        choices=base.choices.Titulacao.choices(),
        max_length=15,
        null=True,
        blank=True,
    )
    admissao = models.DateField(
        verbose_name="Data de admissão",
        null=True,
        blank=True,
        help_text="Data que o servidor entrou em exercício na instituição.",
    )
    lattes = models.URLField(
        verbose_name="Currículo Lattes",
        max_length=100,
        help_text="Endereço para o currículo Lattes.",
        null=True,
        blank=True,
    )
    rt = models.CharField(
        verbose_name="Regime de trabalho",
        max_length=10,
        choices=choices.RegimeTrabalho.choices(),
        null=True,
        blank=True,
    )
    tipo = models.CharField(
        verbose_name="Tipo de servidor",
        choices=base.choices.TipoServidor.choices(),
        max_length=16,
        default=base.choices.TipoServidor.TAE.name,
    )

    objects = ServidorQuerySet.as_manager()

    class Meta:
        verbose_name = "Servidor"
        verbose_name_plural = "Servidores"

    def __str__(self):
        return f"{self.nome} ({self.matricula})"

    @property
    def user(self):
        try:
            user = User.objects.get(username=self.matricula)
        except User.DoesNotExist:
            user = None
        return user

    @property
    def is_tae(self):
        return self.tipo == base.choices.TipoServidor.TAE.name

    @property
    def is_docente(self):
        return self.tipo == base.choices.TipoServidor.DOCENTE.name

    @property
    def is_docente_externo(self):
        return self.tipo == base.choices.TipoServidor.DOCENTE_EXTERNO.name

    @property
    def is_coordenador(self):
        return self.coordenador.exists() or self.coordenador_substituto.exists()

    @property
    def is_diretor_ensino(self):
        return self.campus_dir_ensino.exists() or self.campus_dir_ensino_subs.exists()

    @staticmethod
    def get_by_user(user):
        try:
            servidor = Servidor.objects.get(matricula=user.username)
        except Servidor.DoesNotExist:
            servidor = None
        return servidor


class Docente(Servidor):
    class Meta:
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"
        app_label = "cursos"
        proxy = True

    def save(self, *args, **kwargs):
        self.tipo = base.choices.TipoServidor.DOCENTE.name
        super().save(*args, **kwargs)


class DocenteExterno(Servidor):
    class Meta:
        verbose_name = "Docente Externo"
        verbose_name_plural = "Docentes Externos"
        app_label = "cursos"
        proxy = True

    def save(self, *args, **kwargs):
        self.tipo = base.choices.TipoServidor.DOCENTE_EXTERNO.name
        super().save(*args, **kwargs)


class Campus(models.Model):
    nome = models.CharField(verbose_name="Nome", max_length=55, unique=True)
    sigla = models.CharField(verbose_name="Sigla", max_length=5, unique=True)
    ies = models.ForeignKey(
        IES,
        verbose_name="Instituição de Ensino",
        on_delete=models.CASCADE,
        related_name="campi",
    )
    cidade = models.ForeignKey(Cidade, on_delete=models.CASCADE)
    endereco = models.CharField(verbose_name="Endereço", max_length=255)
    telefone = models.CharField(max_length=15)
    aparece_no_menu = models.BooleanField(
        default=True,
        verbose_name="Exibe URL.",
        help_text="O campus aparecerá no menu de campi no Portal do Estudante.",
    )
    url = models.URLField(verbose_name="URL")
    mapa = models.CharField(
        max_length=1025,
        null=True,
        blank=True,
        help_text="""Endereço da opção "Incorporar Mapa" do Google Maps. Veja este tutorial de como
                                         fazer: https://support.google.com/maps/answer/3544418?hl=pt-BR""",
    )
    diretor_ensino = models.ForeignKey(
        Servidor,
        related_name="campus_dir_ensino",
        verbose_name="Diretor de Ensino",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    diretor_ensino_substituto = models.ForeignKey(
        Servidor,
        related_name="campus_dir_ensino_subs",
        verbose_name="Diretor de Ensino Substituto",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    servidores = models.ManyToManyField(
        User, verbose_name="Servidores", blank=True, related_name="lotacoes"
    )

    class Meta:
        verbose_name_plural = "Campi"
        ordering = ("nome",)

    def __str__(self):
        return self.nome

    def clean(self):
        if self.mapa and not (
            self.mapa.lower().startswith("<iframe") and self.mapa.lower().endswith(">")
        ):
            raise ValidationError(
                {
                    "mapa": """Copie e cole todo o componente <iframe> válido com o formato a seguir:
                                              <iframe src="https://" ... >."""
                }
            )

        if self.diretor_ensino:
            try:
                suaprest.validate_user(self.diretor_ensino.matricula)
            except ValidationError as v:
                raise ValidationError({"diretor_ensino": v.message})

        if self.diretor_ensino_substituto:
            try:
                suaprest.validate_user(self.diretor_ensino_substituto.matricula)
            except ValidationError as v:
                raise ValidationError({"diretor_ensino_substituto": v.message})

        if (
            self.diretor_ensino
            and self.diretor_ensino == self.diretor_ensino_substituto
        ):
            raise ValidationError(
                {
                    "diretor_ensino": "Diretor de Ensino e Substituto não devem ser o mesmo.",
                    "diretor_ensino_substituto": "Diretor de Ensino e Substituto não devem ser o mesmo.",
                }
            )

        if not self.diretor_ensino and self.diretor_ensino_substituto:
            raise ValidationError(
                {"diretor_ensino": "Diretor de Ensino não informado."}
            )

    def cria_usuarios_diretores(self):
        if self.diretor_ensino:
            try:
                suaprest.validate_user(self.diretor_ensino.matricula)
            except ValueError:
                pass

        if self.diretor_ensino_substituto:
            try:
                suaprest.validate_user(self.diretor_ensino_substituto.matricula)
            except ValueError:
                pass

    def adiciona_permissao_diretores(self):
        # O diretor de ensino não é obrigatório.
        try:
            grupo_diretor_ensino = Group.objects.get(name="Diretores de Ensino")
        except Group.DoesNotExist:
            grupo_diretor_ensino = None

        if self.diretor_ensino and grupo_diretor_ensino:
            try:
                user_diretor = User.objects.get(username=self.diretor_ensino.matricula)
                user_diretor.groups.add(grupo_diretor_ensino)
            except User.DoesNotExist:
                pass

        if self.diretor_ensino_substituto and grupo_diretor_ensino:
            try:
                user_diretor_subs = User.objects.get(
                    username=self.diretor_ensino_substituto.matricula
                )
                user_diretor_subs.groups.add(grupo_diretor_ensino)
            except User.DoesNotExist:
                pass

    def remove_permissao_diretores(self):
        grupo_diretor_ensino = Group.objects.get(name="Diretores de Ensino")

        if self.pk:
            original = Campus.objects.get(pk=self.pk)
            if (
                original.diretor_ensino
                and original.diretor_ensino != self.diretor_ensino
            ):
                try:
                    user_orig_diretor = User.objects.get(
                        username=original.diretor_ensino.matricula
                    )
                    user_orig_diretor.groups.remove(grupo_diretor_ensino)
                except User.DoesNotExist:
                    pass
            if (
                original.diretor_ensino_substituto
                and original.diretor_ensino_substituto != self.diretor_ensino_substituto
            ):
                try:
                    user_orig_diretor_subs = User.objects.get(
                        username=original.diretor_ensino_substituto.matricula
                    )
                    user_orig_diretor_subs.groups.remove(grupo_diretor_ensino)
                except User.DoesNotExist:
                    pass

    def save(self, *args, **kwargs):
        self.cria_usuarios_diretores()
        self.adiciona_permissao_diretores()
        #self.remove_permissao_diretores()  
        # # Somente diretores removidos
        super().save()

    def eh_diretor(self, servidor: Servidor):
        return (servidor == self.diretor_ensino) or (
            servidor == self.diretor_ensino_substituto
        )

    def get_absolute_url(self):
        return reverse("campus", args=[str(self.id)])

    def get_src_mapa(self):
        return get_src_mapa(self.mapa)


SIGLAS_DISCIPLINA = ["TCC", "EE", "SI", "ADM", "RC", "TCE", "TV"]


class Disciplina(models.Model):
    nome = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.nome

    def clean(self):
        if self.nome:
            nome_normalizado = normalizar_nome_proprio(self.nome, SIGLAS_DISCIPLINA)
            if (
                Disciplina.objects.filter(nome=nome_normalizado)
                .exclude(pk=self.id)
                .exists()
            ):
                raise ValidationError({"nome": "Disciplina com este Nome já existe."})

    def save(self, *args, **kwargs):
        if self.nome:
            self.nome = normalizar_nome_proprio(self.nome, SIGLAS_DISCIPLINA)
        return super().save(*args, **kwargs)


class Coordenacao(models.Model):
    telefone = models.CharField(
        verbose_name="Telefone",
        max_length=15,
        help_text="Informar o telefone da coordenação.",
    )
    email = models.EmailField(
        verbose_name="E-mail",
        max_length=128,
        help_text="Informar o e-mail da coordenação.",
    )
    coordenador = models.ForeignKey(
        Servidor,
        verbose_name="Coordenador",
        related_name="coordenador",
        on_delete=models.CASCADE,
    )
    substituto = models.ForeignKey(
        Servidor,
        verbose_name="Coordenador substituto",
        related_name="coordenador_substituto",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    curso = models.OneToOneField("cursos.CursoNoCampus", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Coordenação de curso"
        verbose_name_plural = "Coordenações de cursos"

    def __str__(self):
        return f"Coordenação do curso {self.curso}"

    @staticmethod
    def get_by_user(user):
        return Coordenacao.objects.filter(
            Q(coordenador__matricula=user.username)
            | Q(substituto__matricula=user.username)
        ).distinct()

    def cria_usuarios_coordenadores(self):
        if self.coordenador:
            try:
                suaprest.create_user(self.coordenador.matricula)
            except ValueError:
                pass

        if self.substituto:
            try:
                suaprest.create_user(self.substituto.matricula)
            except ValueError:
                pass

    def adiciona_permissao_coordenadores(self):
        grupo_coordenadores = Group.objects.get(
            name="Coordenadores de Cursos dos Campi"
        )

        if self.coordenador:
            try:
                user_coord = User.objects.get(username=self.coordenador.matricula)
                user_coord.groups.add(grupo_coordenadores)
            except User.DoesNotExist:
                pass

        if self.substituto:
            try:
                user_substituto = User.objects.get(username=self.substituto.matricula)
                user_substituto.groups.add(grupo_coordenadores)
            except User.DoesNotExist:
                pass

    def remove_permissao_coordenadores(self):
        grupo_coordenadores = Group.objects.get(
            name="Coordenadores de Cursos dos Campi"
        )

        if self.pk:
            original = Coordenacao.objects.get(pk=self.pk)
            coordenador = original.coordenador
            if coordenador and coordenador != self.coordenador:
                eh_coordenador_outro_curso = coordenador.coordenador.exclude(
                    pk=self.pk
                ).exists()
                eh_substituto_outro_curso = coordenador.coordenador_substituto.exclude(
                    pk=self.pk
                ).exists()
                if not eh_coordenador_outro_curso and not eh_substituto_outro_curso:
                    try:
                        coordenador.user.groups.remove(grupo_coordenadores)
                    except User.DoesNotExist:
                        pass
            substituto = original.substituto
            if substituto and substituto != self.substituto:
                eh_coordenador_outro_curso = substituto.coordenador.exclude(
                    pk=self.pk
                ).exists()
                eh_substituto_outro_curso = substituto.coordenador_substituto.exclude(
                    pk=self.pk
                ).exists()
                if not eh_coordenador_outro_curso and not eh_substituto_outro_curso:
                    try:
                        substituto.user.groups.remove(grupo_coordenadores)
                    except User.DoesNotExist:
                        pass

    def clean(self):
        if self.coordenador_id:
            try:
                suaprest.validate_user(self.coordenador.matricula)
            except ValidationError as v:
                raise ValidationError({"coordenador": v.message})

        if self.substituto_id:
            try:
                suaprest.validate_user(self.substituto.matricula)
            except ValidationError as v:
                raise ValidationError({"substituto": v.message})

        if (
            self.coordenador_id
            and self.substituto_id
            and self.coordenador == self.substituto
        ):
            raise ValidationError(
                {
                    "substituto": "Coordenador Substituto deve ser diferente do coordenador."
                }
            )

    def save(self, *args, **kwargs):
        self.cria_usuarios_coordenadores()
        self.remove_permissao_coordenadores()
        self.adiciona_permissao_coordenadores()
        super().save()


class Curso(models.Model):
    """
    Curso genérico com nome padronizado.
    """

    nome = models.CharField(verbose_name="Nome", max_length=255)
    perfil_unificado = models.TextField(verbose_name="Perfil Unificado")
    nivel_formacao = models.CharField(
        blank=True,
        null=True,
        verbose_name="Nível de Formação",
        choices=choices.NivelFormacao.choices(),
        max_length=16,
    )

    @property
    def nivel_formacao_display(self):
        return choices.NivelFormacao.label(self.nivel_formacao)

    @property
    def is_tecnico(self):
        return self.nivel_formacao == "TECNICO" or self.nivel_formacao == "CONCOMITANTE"

    @property
    def is_graduacao(self):
        return self.nivel_formacao == "GRADUACAO"

    @property
    def is_pos_graduacao(self):
        return self.nivel_formacao == "POSGRADUACAO"

    class Meta:
        verbose_name = "Curso Sistêmico"
        verbose_name_plural = "Cursos Sistêmicos"
        ordering = ("nome",)
        unique_together = (("nome", "nivel_formacao"),)

    def __str__(self):
        return "{} ({})".format(
            self.nome, self.get_nivel_formacao_display() or "Nível não definido"
        )

    def clean(self):
        if not self.nivel_formacao:
            raise ValidationError(
                {"nivel_formacao": "O nível de formação deve ser preenchido."}
            )


class CursoTecnicoManager(models.Manager):
    def get_queryset(self):
        query_set = super().get_queryset()
        query_set = query_set.filter(
            Q(formacao="INTEGRADO") | Q(formacao="SUBSEQUENTE") | Q(formacao="CONCOMITANTE")
        )
        return query_set


class CursoSuperiorManager(models.Manager):
    def get_queryset(self):
        query_set = super().get_queryset()
        query_set = query_set.filter(
            Q(formacao="TECNOLOGICO")
            | Q(formacao="BACHARELADO")
            | Q(formacao="LICENCIATURA")
        )
        return query_set


class CursoPosGraduacaoManager(models.Manager):
    def get_queryset(self):
        query_set = super().get_queryset()
        query_set = query_set.filter(
            Q(formacao="ESPECIALIZACAO")
            | Q(formacao="MESTRADO")
            | Q(formacao="DOUTORADO")
        )
        return query_set


class CursoNoCampusQuerySet(models.QuerySet):
    def ordena_por_formacao(self, *args):
        """Sort patterns by preferred order of Y then -- then N"""
        qs = self.annotate(
            custom_order=models.Case(
                models.When(
                    formacao="INTEGRADO", then=models.Value("Técnico Integrado")
                ),
                models.When(
                    formacao="SUBSEQUENTE", then=models.Value("Técnico Subsequente")
                ),
                models.When(
                    formacao="CONCOMITANTE", then=models.Value("Concomitante")
                ),
                models.When(formacao="TECNOLOGICO", then=models.Value("Tecnológico")),
                models.When(formacao="BACHARELADO", then=models.Value("Bacharelado")),
                models.When(formacao="LICENCIATURA", then=models.Value("Licenciatura")),
                models.When(
                    formacao="ESPECIALIZACAO", then=models.Value("Especialização")
                ),
                models.When(formacao="MESTRADO", then=models.Value("Mestrado")),
                models.When(formacao="DOUTORADO", then=models.Value("Doutorado")),
                output_field=models.CharField(),
            )
        ).order_by("custom_order", *args)
        return qs


class CursoNoCampus(models.Model, HistoryMixin):
    """
    Curso ofertado em um campus.
    """

    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    turno = models.CharField(choices=base.choices.Turno.choices(), max_length=10)
    formacao = models.CharField(
        verbose_name="Formação", choices=choices.Formacao.choices(), max_length=16
    )
    modalidade = models.CharField(choices=choices.Modalidade.choices(), max_length=16)
    perfil = models.TextField(blank=True, null=True, verbose_name="Perfil Profissional")
    perfil_libras = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL de vídeo em Libras do Perfil Profissional",
        help_text='Endereço "src" que aparece na opção de compartilhamento "Incorporar" do YouTube.',
    )
    video_catalogo = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL de vídeo descritivo do curso",
        help_text='Copiar e colar o endereço "src" que aparece na '
        'opção de compartilhamento "Incorporar" do YouTube.',
    )
    codigo = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Código do Curso (e-Mec)",
        help_text="Código do curso cadastrado no e-MEC",
    )
    codigo_suap = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Código Suap",
        help_text="Código utilizado no SUAP para identificar o curso",
    )
    inicio = models.DateField(
        blank=True,
        null=True,
        verbose_name="Início",
        help_text="Data de início do funcionamento do curso",
    )
    termino = models.DateField(
        blank=True,
        null=True,
        verbose_name="Término",
        help_text="Data de encerramento do curso",
    )
    conceito = models.CharField(
        blank=True,
        null=True,
        max_length=50,
        verbose_name="Conceito",
        help_text="Conceito do Curso",
    )
    cpc = models.CharField(
        blank=True,
        max_length=2,
        verbose_name="CPC",
        help_text="Conceito Preliminar de Curso",
    )
    enade = models.CharField(
        blank=True,
        max_length=1,
        verbose_name="ENADE",
        help_text="Nota do Curso no ENADE",
    )
    ch_minima = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Carga Horária Mínima de integralização",
        help_text="Carga horária mínima para a integralização do curso",
    )
    ch_total = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Carga Horária Total",
        help_text="Carga horária total do curso",
    )
    ch_estagio = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Carga Horária de Estágio",
        help_text="Carga horária total de estágio necessária para a integralização do curso",
    )
    ch_tcc = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Carga Horária de TCC",
        help_text="Carga horária necessária para a execução do Trabalho de Conclusão de Curso",
    )
    ch_rel_estagio = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Carga Horária de Relatório de Estágio",
        help_text="Carga horária necessária para a execução do relatório de estágio",
    )
    ch_pratica_docente = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Carga Horária de Prática Docente",
        help_text="Carga horária de prática docente para a integralização do curso. Somente para cursos de Licenciatura.",
    )
    ch_atividades_comp = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Carga Horária de Atividades Complementares",
        help_text="Carga horária mínima de atividades complementares necessárias à integralização do curso",
    )
    periodo_min_int = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Período Mínimo para Integralização",
        help_text="Quantidade Mínima de bimestres/semestres/anos para a integralização do curso",
    )
    forma_acesso = models.ManyToManyField(ProcessoSeletivo, blank=True)
    palavras_chave = models.ManyToManyField(PalavrasChave, blank=True)
    publicado = models.BooleanField(default=False)
    disciplinas_atualizacao = models.DateTimeField(blank=True, null=True)
    excluido = models.BooleanField(
        verbose_name="Excluído",
        help_text="Esta opção removerá a exibição do curso nas listagens",
        default=False,
    )

    objects = CursoNoCampusQuerySet.as_manager()
    cursos_tecnicos = CursoTecnicoManager()
    cursos_superiores = CursoSuperiorManager()
    cursos_pos_graduacao = CursoPosGraduacaoManager()

    def is_administrador_curso(self, user):
        return any(
            [
                user.is_superuser,
                utils.is_admin_sistemico_cursos(user),
                utils.is_diretor_ensino(user),
                utils.is_admin_sistemico_cursos_pos(user),
                utils.is_administrador_cursos_campus(user),
            ]
        )

    @property
    def nome(self):
        return self.curso.nome

    @property
    def is_presencial(self):
        return self.modalidade == choices.Modalidade.PRESENCIAL.name

    @property
    def is_ead(self):
        return self.modalidade == choices.Modalidade.EAD.name

    @property
    def is_concomitante(self):
        return self.formacao == choices.Formacao.CONCOMITANTE.name

    @property
    def is_semipresencial(self):
        return self.modalidade == choices.Modalidade.SEMIPRESENCIAL.name

    @property
    def is_licenciatura(self):
        return self.formacao == choices.Formacao.LICENCIATURA.name

    @property
    def is_bacharelado(self):
        return self.formacao == choices.Formacao.BACHARELADO.name

    @property
    def is_tecnologico(self):
        return self.formacao == choices.Formacao.TECNOLOGICO.name

    @property
    def is_superior(self):
        return self.is_licenciatura or self.is_tecnologico or self.is_bacharelado

    @property
    def is_especializacao(self):
        return self.formacao == choices.Formacao.ESPECIALIZACAO.name

    @property
    def is_mestrado(self):
        return self.formacao == choices.Formacao.MESTRADO.name

    @property
    def is_doutorado(self):
        return self.formacao == choices.Formacao.DOUTORADO.name

    @property
    def is_pos_graduacao(self):
        return self.is_especializacao or self.is_mestrado or self.is_doutorado

    @property
    def is_tecnico(self):
        return self.is_tecnico_integrado or self.is_tecnico_subsequente or self.is_concomitante

    @property
    def is_tecnico_integrado(self):
        return self.formacao == choices.Formacao.INTEGRADO.name

    @property
    def is_concomitante(self):
        return self.formacao == choices.Formacao.CONCOMITANTE.name

    @property
    def is_tecnico_subsequente(self):
        return self.formacao == choices.Formacao.SUBSEQUENTE.name

    def get_perfil(self):
        return self.perfil or self.curso.perfil_unificado

    def documentos_obrigatorios(self):
        if self.curso:
            if self.curso.is_tecnico:
                return TipoDocumento.objects.obrigatorios_nivel_tecnico()
            elif self.curso.is_graduacao:
                return TipoDocumento.objects.obrigatorios_graduacao()
            elif self.curso.is_pos_graduacao:
                return TipoDocumento.objects.obrigatorios_pos_graduacao()
        return TipoDocumento.objects.none()

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ("curso__nome",)

    def __str__(self):
        return "{} em {} - {} - {} ({})".format(
            self.get_formacao_display(),
            self.curso.nome,
            self.get_modalidade_display(),
            self.get_turno_display(),
            self.campus.nome,
        )

    def clean(self):
        super().clean()
        if self.curso_id and self.formacao:
            if (
                self.curso.is_tecnico != self.is_tecnico
                or self.curso.is_graduacao != self.is_superior
                or self.curso.is_pos_graduacao != self.is_pos_graduacao
            ):
                raise ValidationError(
                    f"A formação do curso ({self.get_formacao_display()}) não está de acordo com "
                    f"o nível do curso ({self.curso.get_nivel_formacao_display()})."
                )

            if (
                self.campus_id
                and CursoNoCampus.objects.filter(
                    campus=self.campus,
                    curso=self.curso,
                    turno=self.turno,
                    formacao=self.formacao,
                    modalidade=self.modalidade,
                )
                .exclude(pk=self.id)
                .exists()
            ):
                raise ValidationError(
                    f"Curso {self.get_modalidade_display()} com esta Formação e estes Campus e Turno já existe."
                )

        if self.publicado:
            err_campos_vazios = dict()
            if not self.inicio:
                err_campos_vazios.update(
                    {"inicio": "Este campo deve ser preenchido para publicação."}
                )
            if not self.ch_minima:
                err_campos_vazios.update(
                    {"ch_minima": "Este campo deve ser preenchido para publicação."}
                )

            if self.curso_id and self.curso.is_graduacao:
                if not self.codigo:
                    err_campos_vazios.update(
                        {"codigo": "Este campo deve ser preenchido para publicação."}
                    )
                if not self.enade:
                    err_campos_vazios.update(
                        {"enade": "Este campo deve ser preenchido para publicação."}
                    )
                if self.is_licenciatura and not self.ch_pratica_docente:
                    err_campos_vazios.update(
                        {
                            "ch_pratica_docente": "Em cursos de Licenciatura, "
                            "este campo deve ser preenchido para publicação."
                        }
                    )
            if err_campos_vazios.items():
                err_campos_vazios.update(
                    {
                        "publicado": "Para que as informações do Curso sejam publicadas, os campos indicados devem ser preenchidos."
                    }
                )
                raise ValidationError(err_campos_vazios)
        if self.termino and self.inicio and self.termino <= self.inicio:
            raise ValidationError(
                {"termino": "A data de término deve ser maior que a de início."}
            )

    def save(self, *args, **kwargs):
        if not self.perfil:
            self.perfil = self.curso.perfil_unificado
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("curso", args=[str(self.id)])


class AtoRegulatorio(models.Model):
    curso = models.ForeignKey(CursoNoCampus, on_delete=models.CASCADE)
    tipo = models.ForeignKey(TipoAtoRegulatorio, on_delete=models.CASCADE)
    arquivo = models.FileField(
        max_length=255,
        upload_to=generate_atoregulatorio_curso_path,
        help_text="Apenas arquivos .pdf no tamanho máximo de 2MB.",
        validators=[validate_file_size, validate_file_type],
    )
    descricao = models.CharField(verbose_name="Descrição", max_length=255)
    numero = models.IntegerField(verbose_name="Número")
    ano = models.IntegerField()

    class Meta:
        verbose_name = "Ato Regulatorio"
        verbose_name_plural = "Atos Regulatorios"

    def __str__(self):
        return f"{self.tipo} {self.numero}/{self.ano}"

    def clean(self):
        if self.ano and (self.ano < 1910 or self.ano > datetime.now().year):
            raise ValidationError(
                {
                    "ano": "O ano informado deve ser menor ou igual a {} e maior que 1909.".format(
                        datetime.now().year
                    )
                }
            )


class Historico(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    curso_alterado = models.ForeignKey(Curso, on_delete=models.CASCADE)
    atributo_alterado = models.CharField(max_length=20)
    valor_antigo = models.TextField()
    valor_novo = models.TextField()
    data_alteracao = models.DateField(auto_now="true")

    class Meta:
        verbose_name = "Histórico"
        verbose_name_plural = "Histórico"

    def __str__(self):
        return f"{self.usuario} alterou {self.curso_alterado} em {self.data_alteracao}"


class Documento(models.Model):
    curso = models.ForeignKey(CursoNoCampus, on_delete=models.CASCADE)
    descricao = models.CharField(verbose_name="Descrição", max_length=255)
    arquivo = models.FileField(
        verbose_name="Arquivo",
        upload_to=generate_documento_curso_path,
        help_text="Apenas arquivos .pdf no tamanho máximo de 2MB.",
    )
    tipo = models.ForeignKey("cursos.TipoDocumento", on_delete=models.CASCADE)

    def __str__(self):
        return self.descricao

    def clean(self):
        max_size_2mb = 2097152
        max_size_8mb = 8388608
        if self.arquivo:
            try:
                filesize = self.arquivo.file.size
                if self.tipo_id and (
                    self.tipo.nome == "Projetos" or self.tipo.nome == "PPC"
                ):
                    if filesize > max_size_8mb:
                        raise ValidationError("Arquivo não pode ser maior que 8MB!")
                else:
                    if filesize > max_size_2mb:
                        raise ValidationError("Arquivo não pode ser maior que 2MB!")
            except FileNotFoundError as e:
                if not settings.DEBUG:
                    raise e


class Polo(models.Model):
    cidade = models.ForeignKey(Cidade, on_delete=models.CASCADE)
    horario_funcionamento = models.CharField(
        verbose_name="Horário de Funcionamento", max_length=100
    )
    endereco = models.CharField(verbose_name="Endereço", max_length=255)
    telefone = models.CharField(max_length=15)
    mapa = models.CharField(
        max_length=1025,
        help_text='Endereço da opção "Incorporar Mapa" do Google Maps. Veja este tutorial de como fazer: https://support.google.com/maps/answer/3544418?hl=pt-BR',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Polo"
        verbose_name_plural = "Polos"
        ordering = ["cidade__nome"]

    def __str__(self):
        return str(self.cidade)

    def clean(self):
        if self.mapa and not (
            self.mapa.lower().startswith("<iframe") and self.mapa.lower().endswith(">")
        ):
            raise ValidationError(
                {
                    "mapa": 'Copie e cole todo o componente <iframe> válido com o formato a seguir: <iframe src="https://" ... >.'
                }
            )

    def get_absolute_url(self):
        return reverse("polo", args=[str(self.id)])

    def get_src_mapa(self):
        return get_src_mapa(self.mapa)


class DisciplinaCurso(models.Model):
    curso = models.ForeignKey(CursoNoCampus, on_delete=models.CASCADE)
    docentes = models.ManyToManyField(Servidor)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    periodo = models.IntegerField(verbose_name="Período ou Ano")
    ch = models.IntegerField(verbose_name="Carga Horária")  # Carga horaria
    plano = models.FileField(
        max_length=255,
        upload_to=generate_plano_disciplina_path,
        blank=True,
        null=True,
        help_text="Apenas arquivos .pdf no tamanho máximo de 2MB.",
        validators=[validate_file_size, validate_file_type],
    )

    def __str__(self):
        return f"{self.disciplina} ({self.curso})"

    class Meta:
        verbose_name = "Disciplina do Curso"
        verbose_name_plural = "Disciplinas dos Cursos"


class VagaCurso(models.Model):
    curso = models.ForeignKey(CursoNoCampus, on_delete=models.CASCADE)
    polo = models.ForeignKey(Polo, null=True, blank=True, on_delete=models.SET_NULL)
    vagas_s1 = models.PositiveIntegerField(verbose_name="Vagas no 1º Semestre")
    vagas_s2 = models.PositiveIntegerField(verbose_name="Vagas no 2º Semestre")

    class Meta:
        verbose_name = "Vaga"
        verbose_name_plural = "Vagas"


class CursoSelecao(CursoNoCampus):
    polo = models.ForeignKey(
        Polo,
        verbose_name="Polo EAD",
        related_name="cursos_selecao",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Curso para seleção"
        verbose_name_plural = "Cursos para seleções"

    def __str__(self):
        string = super().__str__()
        if self.polo:
            return f"{string} - Polo {self.polo}"
        return string
