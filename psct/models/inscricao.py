import os
from datetime import datetime
from decimal import Decimal, getcontext, ROUND_HALF_UP

import reversion
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, F, Q
from django.db.models.aggregates import Sum
from django.urls import reverse
from django.utils.functional import cached_property

from base import validators
from cursos import models as c_models
from editais.models import Edital
from processoseletivo.models import Modalidade as ModalidadePadrao, ModalidadeEnum
from psct.dbfields import DocumentFileField
from psct.models.candidato import Candidato
from .. import querysets

ZERO = Decimal("0.0")


LABEL_ACEITE = """DECLARO, para os fins de direito, sob as penas da lei, que as informações que apresento para a inscrição
são fiéis à verdade e condizentes com a realidade dos fatos. Fico ciente, portanto, que a falsidade desta
declaração configura-se em crime previsto no Código Penal Brasileiro e passível de apuração na forma da Lei."""


def format_curso(curso):
    return "{} - {} - {}".format(
        curso.get_formacao_display(), curso.curso.nome, curso.get_turno_display()
    )


@reversion.register()
class ProcessoInscricao(models.Model):
    INTEGRADO = "INTEGRADO"
    SUBSEQUENTE = "SUBSEQUENTE"
    GRADUACAO = "GRADUACAO"
    CONCOMITANTE = "CONCOMITANTE"
    FORMACAO_CHOICES = (
        ("INTEGRADO", "Técnico Integrado"),
        ("SUBSEQUENTE", "Técnico Subsequente"),
        ("GRADUACAO", "Graduação"),
        ("CONCOMITANTE", "Concomitante"),
    )
    edital = models.OneToOneField(
        Edital,
        verbose_name="Edital",
        related_name="processo_inscricao",
        on_delete=models.PROTECT,
    )
    formacao = models.CharField(
        max_length=20, verbose_name="Formação", choices=FORMACAO_CHOICES
    )
    cursos = models.ManyToManyField(
        c_models.CursoSelecao,
        verbose_name="Cursos",
        limit_choices_to={"excluido": False},
    )
    multiplicador = models.PositiveSmallIntegerField(
        verbose_name="Multiplicador",
        help_text="Quantidade de candidatos classificados por vaga",
        default=5,
    )
    data_inicio = models.DateField(
        verbose_name="Data de início do período de inscrição"
    )
    data_encerramento = models.DateField(
        verbose_name="Data de encerramento do período de inscrição"
    )
    data_inicial_comprovante = models.DateTimeField(
        verbose_name="Data inicial de emissão do comprovante de inscrição",
        help_text="Se a data e a hora inseridas forem anteriores a este momento, "
        "o comprovante será liberado após salvar.",
        blank=True,
        null=True,
    )
    data_final_comprovante = models.DateTimeField(
        verbose_name="Data final de emissão do comprovante de inscrição",
        help_text="A data e o hora inseridas devem ser posteriores à data inicial "
        "de emissão de comprovante.",
        blank=True,
        null=True,
    )
    data_resultado_preliminar = models.DateTimeField(
        verbose_name="Data a partir de quando o candidato poderá visualizar o resultado preliminar",
        blank=True,
        null=True,
    )
    possui_segunda_opcao = models.BooleanField(
        verbose_name="Disponibiliza a segunda opção de curso para os candidatos?",
        default=False,
    )

    class Meta:
        verbose_name = "Processo de Inscrição do Edital"
        verbose_name_plural = "Processos de Inscrição dos Editais"
        ordering = ("edital",)

    @property
    def em_periodo_inscricao(self):
        return self.data_inicio <= datetime.now().date() <= self.data_encerramento

    @property
    def pode_emitir_comprovante(self):
        if self.data_inicial_comprovante and self.data_final_comprovante:
            return (
                self.data_inicial_comprovante
                < datetime.now()
                < self.data_final_comprovante
            )
        if self.data_inicial_comprovante:
            return self.data_inicial_comprovante < datetime.now()
        return False

    @property
    def pode_acompanhar_inscricao(self):
        return datetime.now().date() >= self.data_encerramento

    @property
    def pode_alterar_funcao_segunda_opcao(self):
        return not self.edital.inscricao_set.exists()

    def __str__(self):
        return f"Cursos do {self.edital}"

    def clean(self):
        if self.id:
            possui_segunda_opcao_stored = ProcessoInscricao.objects.filter(
                id=self.id
            ).values(
                "possui_segunda_opcao"
            ).first()["possui_segunda_opcao"]

            if (
                self.possui_segunda_opcao != possui_segunda_opcao_stored and
                not self.pode_alterar_funcao_segunda_opcao
            ):
                raise ValidationError(
                    {
                        "possui_segunda_opcao":
                            "Este valor não pode ser alterado porque já "
                            "existem inscrições associadas ao edital."
                    }
                )

        if (
            self.data_inicial_comprovante
            and self.data_inicial_comprovante.date() <= self.data_encerramento
        ):
            raise ValidationError(
                {
                    "data_inicial_comprovante": "A data inicial de emissão de comprovante não pode ser igual ou inferior à data de encerramento."
                }
            )
        if self.data_final_comprovante:
            if self.data_final_comprovante.date() <= self.data_encerramento:
                raise ValidationError(
                    {
                        "data_final_comprovante": "A data final de emissão de comprovante não pode ser igual ou anterior à data de encerramento."
                    }
                )
            if not self.data_inicial_comprovante:
                raise ValidationError(
                    {
                        "data_inicial_comprovante": "Data inicial de emissão do comprovante não informada."
                    }
                )
            else:
                if self.data_inicial_comprovante >= self.data_final_comprovante:
                    raise ValidationError(
                        {
                            "data_final_comprovante": "A data final de emissão de comprovante não pode ser igual ou"
                            " anterior à data de início de emissão."
                        }
                    )

        if self.data_resultado_preliminar and self.data_encerramento:
            if self.data_resultado_preliminar.date() < self.data_encerramento:
                raise ValidationError(
                    {
                        "data_resultado_preliminar": "A Data do resultado preliminar deve ser superior à data de encerramento"
                    }
                )

    @property
    def is_curso_tecnico(self):
        return self.formacao in (self.INTEGRADO, self.SUBSEQUENTE, self.CONCOMITANTE)

    @property
    def is_graduacao(self):
        return self.formacao == self.GRADUACAO


@reversion.register()
class Modalidade(models.Model):
    equivalente = models.OneToOneField(
        ModalidadePadrao,
        verbose_name="Modalidade equivalente",
        help_text="Selecione a equivalência da modalidade que está sendo editada",
        related_name="equivalencia_psct",
        on_delete=models.CASCADE,
    )
    texto = models.TextField(
        verbose_name="Texto", help_text="Texto que será exibido para o candidato"
    )

    objects = querysets.ModalidadeQuerySet.as_manager()

    def __str__(self):
        return self.texto or self.equivalente.nome

    class Meta:
        verbose_name = "Modalidade de cota"
        verbose_name_plural = "Modalidades de cota"
        ordering = ("texto",)

    @property
    def is_ampla(self):
        return self.id == ModalidadeEnum.ampla_concorrencia

    @property
    def resumo(self):
        return self.equivalente.resumo if self.equivalente.resumo else str(self)

    def por_nivel_formacao(self, processo_inscricao: ProcessoInscricao) -> str:
        """Retorna descrição da modalidade de acordo
        com o nível de formação do Processo de Inscrição.

        1 - Para curso superior e modalidade de escola pública,
        substitui ENSINO FUNDAMENTAL por ENSINO MÉDIO
        2 - Para curso superior, quando a modalidade for ARA, inserir o Campus Picuí
        """
        modalidade = str(self)
        if processo_inscricao.is_graduacao:
            if self.equivalente.is_escola_publica():
                modalidade = modalidade.replace('ENSINO FUNDAMENTAL', 'ENSINO MÉDIO')
            if self.equivalente.is_cota_rural():
                modalidade = modalidade.replace('IFPB - CAMPUS SOUSA', 'IFPB NOS CAMPI PICUÍ E SOUSA')
        return modalidade


class InscricaoValidaManager(models.Manager):
    def get_queryset(self):
        tecnico = Q(comprovantes__isnull=False) & ~Q(
            edital__processo_inscricao__formacao=ProcessoInscricao.GRADUACAO
        )
        superior = Q(comprovantes__isnull=True) & Q(
            edital__processo_inscricao__formacao=ProcessoInscricao.GRADUACAO
        )
        return (
            super()
            .get_queryset()
            .filter(tecnico | superior, cancelamento__isnull=True, aceite=True,)
            .distinct()
        )


class SituacaoInscricaoDisplay:
    def __str__(self):
        return self.get_mensagem()

    def get_mensagem(self):
        raise TypeError()

    def get_css_class(self):
        raise TypeError()


class SituacaoClassificada(SituacaoInscricaoDisplay):
    def __init__(self, classificacao, classificacao_cota=None, em_espera=False):
        self.classificacao = classificacao
        self.classificacao_cota = classificacao_cota
        self.em_espera = em_espera

    def get_mensagem(self):
        if self.em_espera:
            return "Em lista de espera"
        if self.classificacao_cota:
            return "Classificado(a). {}º na classificação geral. {}º na modalidade de cota".format(
                self.classificacao, self.classificacao_cota
            )
        return f"Classificado(a). {self.classificacao}º na classificação geral."

    def get_css_class(self):
        if self.em_espera:
            return "pendente"
        return "success"


class SituacaoNaoClassificada(SituacaoInscricaoDisplay):
    def get_mensagem(self):
        return "Apto(a) mas não classificado(a)"

    def get_css_class(self):
        return "indeferido"


class SituacaoIndeferida(SituacaoInscricaoDisplay):
    def __init__(self, indeferimento):
        self.indeferimento = indeferimento

    def get_mensagem(self):
        return f"Desclassificado(a). Motivo: {self.indeferimento}"

    def get_css_class(self):
        return "indeferido"


class SituacaoAguardandoResultado(SituacaoInscricaoDisplay):
    def get_mensagem(self):
        return "Inscrição aguardando avaliação"

    def get_css_class(self):
        return "pendente"


class SituacaoInscricaoNaoConcluida(SituacaoInscricaoDisplay):
    def get_mensagem(self):
        return "Inscrição não concluída"

    def get_css_class(self):
        return "pendente"


class SituacaoInscricaoCancelada(SituacaoInscricaoDisplay):
    def get_mensagem(self):
        return "Você cancelou a inscrição."

    def get_css_class(self):
        return "indeferido"


@reversion.register()
class Inscricao(models.Model):
    candidato = models.ForeignKey(
        Candidato, verbose_name="Candidato", on_delete=models.PROTECT
    )
    nome = models.CharField(max_length=100, verbose_name="Nome", null=True)
    cpf = models.CharField(
        max_length=14,
        verbose_name="CPF",
        validators=[validators.cpf_validator],
        null=True,
    )
    edital = models.ForeignKey(Edital, verbose_name="Edital", on_delete=models.PROTECT)
    curso = models.ForeignKey(
        c_models.CursoSelecao, verbose_name="Curso", on_delete=models.PROTECT
    )
    curso_segunda_opcao = models.ForeignKey(
        c_models.CursoSelecao,
        verbose_name="Curso",
        on_delete=models.PROTECT,
        related_name="inscricao_psct_2a_opcao",
        null=True,
        blank=True,
    )
    com_segunda_opcao = models.BooleanField(
        default=False,
        verbose_name="Desejo me inscrever também para uma segunda opção de curso."
    )
    ano_enem = models.IntegerField(
        verbose_name="Ano de realização do ENEM", null=True, blank=True
    )
    modalidade_cota = models.ForeignKey(
        Modalidade,
        verbose_name="Modalidade da Cota",
        related_name="inscricoes_psct",
        default=ModalidadeEnum.ampla_concorrencia,
        on_delete=models.PROTECT,
    )
    aceite = models.BooleanField(default=False, verbose_name=LABEL_ACEITE)
    data_criacao = models.DateTimeField(
        verbose_name="Data de criação", auto_now_add=True
    )
    data_atualizacao = models.DateTimeField(
        verbose_name="Data de atualização", auto_now=True
    )

    objects = models.Manager()
    validas = InscricaoValidaManager()

    class Meta:
        verbose_name = "Inscrição"
        verbose_name_plural = "Inscrições"
        unique_together = ("candidato", "edital")
        permissions = (
            ("recover_inscricao", "Administrador pode recuperar dados de inscrição"),
            ("list_inscricao", "Administrador pode listar inscrições"),
            ("add_list_inscritos", "Administrador pode criar listar de inscrições"),
        )

    def __str__(self):
        return f"Inscrição de {self.candidato} em {self.edital}"

    @property
    def inscricao_pre_analise(self):
        from psct.models.analise import InscricaoPreAnalise

        return InscricaoPreAnalise.objects.filter(
            fase__edital=self.edital, candidato=self.candidato
        ).last()

    def save(self, *args, **kwargs):
        if not self.id and self.candidato_id:
            self.nome = self.candidato.nome.upper()
            self.cpf = self.candidato.cpf
        super().save(*args, **kwargs)
        try:
            self.pontuacao
        except Inscricao.pontuacao.RelatedObjectDoesNotExist:
            if self.is_selecao_curso_tecnico:
                PontuacaoInscricao.objects.create(inscricao=self)

    def get_anos_requeridos(self):
        if self.is_selecao_curso_tecnico:
            if self.curso.formacao == "INTEGRADO" or self.curso.formacao == "CONCOMITANTE":
                return [6, 7, 8]
            elif self.curso.formacao == "SUBSEQUENTE":
                return [1, 2]
            else:
                raise ValueError("Formação errada")

    @property
    def is_integrado(self):
        return self.curso.formacao == "INTEGRADO"

    def is_owner(self, user):
        return self.candidato.user == user

    @property
    def em_periodo_inscricao(self):
        processo = self.edital.processo_inscricao
        return (
            processo.data_inicio <= datetime.now().date() <= processo.data_encerramento
        )

    @cached_property
    def processo_inscricao(self):
        return self.edital.processo_inscricao

    @property
    def pode_alterar(self):
        return self.em_periodo_inscricao and not self.is_cancelada

    def clean(self):
        super().clean()
        if (
            not self.edital.processo_inscricao.possui_segunda_opcao and
            self.curso_segunda_opcao
        ):
            raise ValidationError(
                {
                    "com_segunda_opcao":
                        "Não é permitido selecionar uma segunda opção de curso."
                }
            )
        if not self.em_periodo_inscricao:
            raise ValidationError("Impossível alterar objeto")

    def get_absolute_url(self):
        return reverse("visualizar_inscricao_psct", kwargs={"pk": self.id})

    def pode_inserir_notas(self):
        if self.is_selecao_curso_tecnico:
            if hasattr(self, "pontuacao"):
                return self.pontuacao.notas.exists() and self.pode_alterar
            else:
                return False
        return False

    def pode_inserir_comprovantes(self):
        if self.is_selecao_curso_tecnico:
            notas = self.pontuacao.notas.exclude(
                Q(portugues=ZERO)
                & Q(matematica=ZERO)
                & Q(historia=ZERO)
                & Q(geografia=ZERO)
            ).exists()
            return self.pode_alterar and (self.comprovantes.exists() or notas)
        return False

    @property
    def is_concluida(self):
        if self.is_selecao_curso_tecnico:
            return self.aceite and not self.is_cancelada and self.comprovantes.exists()
        return self.aceite and not self.is_cancelada

    def pode_visualizar_inscricao(self):
        return self.is_concluida

    @property
    def is_cancelada(self):
        try:
            self.cancelamento
            return True
        except CancelamentoInscricao.DoesNotExist:
            return False

    @property
    def is_apagou_notas(self):
        return not self.aceite and self.comprovantes.exists()

    @property
    def is_periodo_deferimento(self):
        return self.edital.processo_inscricao.pode_emitir_comprovante

    @property
    def is_deferida(self):
        if self.is_periodo_deferimento:
            return self.comprovantes.exists() and self.aceite and not self.is_cancelada
        return False

    @property
    def is_ampla_concorrencia(self):
        return self.modalidade_cota.id == ModalidadeEnum.ampla_concorrencia

    def get_situacao_resultado(self, resultado):
        indeferimento = resultado.get_indeferimento(self)
        if indeferimento:
            return SituacaoIndeferida(indeferimento)
        else:
            classificacao_geral, classificacao_cota = resultado.get_classificacao(self)
            if resultado.is_classificado(self):
                if self.is_ampla_concorrencia:
                    return SituacaoClassificada(classificacao_geral)
                else:
                    return SituacaoClassificada(classificacao_geral, classificacao_cota)
            elif resultado.em_lista_espera(self):
                return SituacaoClassificada(
                    classificacao_geral, classificacao_cota, em_espera=True
                )
            else:
                return SituacaoNaoClassificada()

    def get_situacao(self):
        if self.is_cancelada:
            return SituacaoInscricaoCancelada()
        elif self.is_concluida and self.pode_ver_resultado_preliminar and self.has_resultado:
            return self.get_situacao_resultado(self.get_resultado_edital().resultado)
        elif self.is_concluida and not self.edital.processo_inscricao.em_periodo_inscricao:
            return SituacaoAguardandoResultado()
        elif not self.is_concluida:
            return SituacaoInscricaoNaoConcluida()
        else:
            return

    @property
    def has_resultado(self):
        return hasattr(self.edital, "resultado_preliminar") or hasattr(self.edital, "resultado")

    def get_resultado_edital(self):
        if hasattr(self.edital, "resultado"):
            return self.edital.resultado
        if hasattr(self.edital, "resultado_preliminar"):
            return self.edital.resultado_preliminar

    def get_resultado(self):
        resultado_edital = self.get_resultado_edital()
        if resultado_edital:
            return resultado_edital.resultado.get_resultado_inscricao(self)

    @property
    def is_resultado_final(self):
        resultado = self.get_resultado_edital()
        if resultado:
            return resultado.is_final()
        return False

    @property
    def pode_ver_resultado_preliminar(self):
        if self.edital.processo_inscricao.data_resultado_preliminar:
            return datetime.now() > self.edital.processo_inscricao.data_resultado_preliminar
        return False

    def get_extrato_pontuacao(self):
        resultado = self.get_resultado()
        pontuacao_homologador = (
            resultado.inscricao_preanalise.pontuacoes_homologadores.first()
        )
        if pontuacao_homologador:
            return pontuacao_homologador
        return self.pontuacao

    def atualizar_informacoes_candidato(self):
        if self.em_periodo_inscricao:
            self.cpf = self.candidato.cpf
            self.nome = self.candidato.nome
            self.save()

    def pode_desfazer_cancelamento(self):
        pode = False
        if len(self.candidato.inscricao_set.all()) == 1:
            pode = True
        return pode

    @cached_property
    def is_selecao_curso_tecnico(self):
        return self.processo_inscricao.is_curso_tecnico

    @cached_property
    def is_selecao_graduacao(self):
        return self.processo_inscricao.is_graduacao


class NotasEnemMixin:
    def areas_tematicas(self) -> list:
        return ["portugues", "matematica", "redacao", "ciencias_natureza", "ciencias_humanas"]


class NotasCursosSuperioresMixin:
    def desempate(self) -> list:
        return ["-redacao", "-matematica", "-portugues"]


class EstrategiaCalculoNota:
    resultado = {}

    def areas_tematicas(self) -> list:
        raise NotImplementedError("Áreas/disciplinas para o cálculo de notas não foram definidas.")

    def desempate(self) -> list:
        raise NotImplementedError("Lista para ordenação de desempate não foi definida.")

    def get_notas(self):
        pass

    def get_resultado(self):
        return self.resultado

    def calcular(self) -> Decimal:
        raise NotImplementedError("Estratégia de cálculo de notas não definida.")


class MaiorNotaEnemEstrategia(NotasEnemMixin, NotasCursosSuperioresMixin, EstrategiaCalculoNota):

    def __init__(self, inscricao: Inscricao):
        self.inscricao = inscricao

    def get_notas(self):
        if hasattr(self.inscricao, 'pontuacao'):
            return self.inscricao.pontuacao.notas.all()
        return NotaAnual.objects.none()

    def calcular(self):
        def sum_query(fields):
            main_field = F(fields.pop(0))
            for i, field in enumerate(fields):
                main_field = main_field + F(fields[i])
            return main_field
        notas = self.get_notas()
        total_disciplinas = len(self.areas_tematicas())
        maior_nota = notas.annotate(
            media=(sum_query(self.areas_tematicas()) / total_disciplinas)
        ).order_by(
            "-media", *self.desempate()
        ).first()
        self.resultado = {
            "valor": maior_nota.media,
            "portugues": maior_nota.portugues,
            "matematica": maior_nota.matematica,
            "ciencias_natureza": maior_nota.ciencias_natureza,
            "ciencias_humanas": maior_nota.ciencias_humanas,
            "redacao": maior_nota.redacao,
            "ano": maior_nota.ano,
        }


class MediaEnemEstrategia(NotasEnemMixin, EstrategiaCalculoNota):

    def __init__(self, inscricao: Inscricao):
        self.inscricao = inscricao

    def desempate(self) -> list:
        return []

    def calcular(self):
        def sum_query(fields):
            main_field = F(fields.pop(0))
            for i, field in enumerate(fields):
                main_field = main_field + F(fields[i])
            return main_field
        notas = self.get_notas()
        total_disciplinas = len(self.areas_tematicas())
        nota_media = notas.annotate(
            media=(sum_query(self.areas_tematicas()) / total_disciplinas)
        ).aggegate(media_total=Avg('media'))["media_total"]
        self.resultado = {
            "valor": nota_media,
            "portugues": notas.aggregate(media_pt=Avg("portugues"))["media_pt"],
            "matematica": notas.aggregate(media_mt=Avg("matematica"))["media_mt"],
            "ciencias_natureza": notas.aggregate(media_cn=Avg("ciencias_natureza"))["media_cn"],
            "ciencias_humanas": notas.aggregate(media_ch=Avg("ciencias_humanas"))["media_ch"],
            "redacao": notas.aggregate(media_redacao=Avg("redacao"))["media_redacao"],
        }


class PontuacaoBase:
    def get_pontuacao_graducao(self):
        estrategia = MaiorNotaEnemEstrategia(inscricao=self.inscricao)
        estrategia.calcular()
        return estrategia.get_resultado()["valor"]

    def get_pontuacao_tecnico(self):
        pt = self.get_pontuacao_portugues()
        mt = self.get_pontuacao_matematica()
        ht = self.get_pontuacao_historia()
        ge = self.get_pontuacao_geografia()
        resultado = (pt + mt + ht + ge) / 4
        return resultado

    def get_pontuacao_subsequente(self):
        pt = self.get_pontuacao_portugues()
        mt = self.get_pontuacao_matematica()
        resultado = (pt + mt) / 2
        return resultado

    def get_pontuacao_total(self):
        if self.is_curso_tecnico:
            if self.inscricao.curso.formacao == "INTEGRADO":
                return self.get_pontuacao_tecnico()
            return self.get_pontuacao_subsequente()
        else:
            return self.get_pontuacao_graduacao()

    def get_anos_requeridos(self):
        if self.is_curso_tecnico:
            if not self.ensino_regular:
                return [0]
            return self.inscricao.get_anos_requeridos()
        else:
            return self.notas.values_list('ano', flat=True)

    def get_valor_disciplina(self, disciplina):
        notas = [
            self.get_valor_disciplina_por_ano(disciplina, ano)
            for ano in self.get_anos_requeridos()
        ]
        total = len(notas)
        soma = sum(nota for nota in notas)
        valor = soma / total
        return valor

    def get_valor_disciplina_por_ano(self, disciplina, ano):
        qs = self.notas.filter(ano=ano)
        if qs.exists():
            notas = qs.first()
            return getattr(notas, disciplina)
        else:
            return ZERO

    def get_pontuacao_portugues(self):
        return self.get_valor_disciplina("portugues")

    def get_pontuacao_matematica(self):
        return self.get_valor_disciplina("matematica")

    def get_pontuacao_historia(self):
        return self.get_valor_disciplina("historia")

    def get_pontuacao_historia_display(self):
        return round(self.get_pontuacao_historia(), 2)

    def get_pontuacao_geografia_display(self):
        return round(self.get_pontuacao_geografia(), 2)

    def get_pontuacao_geografia(self):
        return self.get_valor_disciplina("geografia")

    def update_pontuacao(self):
        getcontext().rounding = ROUND_HALF_UP
        if self.is_curso_tecnico:
            self.valor = round(self.get_pontuacao_total(), 2)
            self.valor_pt = round(self.get_pontuacao_portugues(), 2)
            self.valor_mt = round(self.get_pontuacao_matematica(), 2)
        else:
            estrategia = MaiorNotaEnemEstrategia(inscricao=self.inscricao)
            estrategia.calcular()
            resultado = estrategia.get_resultado()
            self.valor = resultado["valor"]
            self.valor_pt = resultado["portugues"]
            self.valor_mt = resultado["matematica"]
            self.valor_redacao = resultado["redacao"]
            self.nascimento = self.inscricao.candidato.nascimento
        self.save()

    def criar_notas(self):
        if self.inscricao.processo_inscricao.is_curso_tecnico:
            if not self.notas.exists():
                if self.ensino_regular:
                    for ano in self.inscricao.get_anos_requeridos():
                        NotaAnual.objects.create(pontuacao=self, ano=ano)
                else:
                    NotaAnual.objects.create(pontuacao=self, ano=0)

    def apagar_notas(self):
        self.notas.all().delete()
        self.inscricao.aceite = False
        self.inscricao.save()

    def get_pontuacao_redacao(self):
        return self.get_valor_disciplina("redacao")

    def get_pontuacao_ciencias_natureza(self):
        return self.get_valor_disciplina("ciencias_natureza")

    def get_pontuacao_ciencias_humanas(self):
        return self.get_valor_disciplina("ciencias_humanas")

    def get_pontuacao_redacao_display(self):
        return round(self.get_pontuacao_redacao(), 2)

    def get_pontuacao_ciencias_natureza_display(self):
        return round(self.get_pontuacao_ciencias_natureza(), 2)

    def get_pontuacao_ciencias_humanas_display(self):
        return round(self.get_pontuacao_ciencias_humanas(), 2)

    @cached_property
    def is_curso_tecnico(self):
        return self.inscricao.processo_inscricao.is_curso_tecnico

    @cached_property
    def is_curso_graduacao(self):
        return self.inscricao.processo_inscricao.is_graduacao


@reversion.register()
class PontuacaoInscricao(models.Model, PontuacaoBase):
    inscricao = models.OneToOneField(
        Inscricao,
        verbose_name="Inscrição",
        related_name="pontuacao",
        on_delete=models.PROTECT,
    )
    valor = models.DecimalField(
        verbose_name="Valor", max_digits=5, decimal_places=2, default=ZERO
    )

    # PSCT
    valor_pt = models.DecimalField(
        verbose_name="Valor de desempate PT",
        max_digits=5,
        decimal_places=2,
        default=ZERO,
    )
    valor_mt = models.DecimalField(
        verbose_name="Valor de desempate MT",
        max_digits=5,
        decimal_places=2,
        default=ZERO,
    )
    ensino_regular = models.BooleanField(
        verbose_name="Candidato cursou o ensino regular?", default=False
    )

    # PSCS
    #################
    valor_redacao = models.DecimalField(
        verbose_name="Valor de desempate - Redação",
        max_digits=5,
        decimal_places=2,
        default=ZERO,
    )
    nascimento = models.DateField(
        verbose_name="Valor de desempate - Idade", null=True, blank=True
    )
    #################

    data_criacao = models.DateTimeField(
        verbose_name="Data de criação", auto_now_add=True
    )
    data_atualizacao = models.DateTimeField(
        verbose_name="Data de atualização", auto_now=True
    )

    class Meta:
        verbose_name = "Pontuação da Inscrição"
        verbose_name_plural = "Pontuações de Inscrição"

    def __str__(self):
        return f"Pontuação Informada de {self.inscricao}"


@reversion.register()
class NotaAnual(models.Model):
    ANO_CHOICES = [(0, 0), (6, 6), (7, 7), (8, 8), (1, 1), (2, 2)]  # Supletivo ou ENEM
    pontuacao = models.ForeignKey(
        PontuacaoInscricao,
        verbose_name="Pontuação da Inscrição",
        related_name="notas",
        on_delete=models.PROTECT,
    )
    ano = models.PositiveSmallIntegerField(verbose_name="Ano")
    portugues = models.DecimalField(
        verbose_name="Português", max_digits=5, decimal_places=2, default=ZERO
    )
    matematica = models.DecimalField(
        verbose_name="Matemática", max_digits=5, decimal_places=2, default=ZERO
    )
    # PSCT
    #################s
    historia = models.DecimalField(
        verbose_name="História", max_digits=5, decimal_places=2, default=ZERO
    )
    geografia = models.DecimalField(
        verbose_name="Geografia", max_digits=5, decimal_places=2, default=ZERO
    )
    #################

    # PSCS
    #################
    redacao = models.DecimalField(
        verbose_name="Redação", max_digits=5, decimal_places=2, default=ZERO
    )
    ciencias_natureza = models.DecimalField(
        verbose_name="Ciências da natureza",
        max_digits=5,
        decimal_places=2,
        default=ZERO,
    )
    ciencias_humanas = models.DecimalField(
        verbose_name="Ciências humanas", max_digits=5, decimal_places=2, default=ZERO
    )
    #################
    data_criacao = models.DateTimeField(
        verbose_name="Data de criação", auto_now_add=True
    )
    data_atualizacao = models.DateTimeField(
        verbose_name="Data de atualização", auto_now=True
    )

    class Meta:
        verbose_name = "Nota Anual"
        verbose_name_plural = "Notas Anuais"
        ordering = ("ano",)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.pontuacao.update_pontuacao()

    def __str__(self):
        if self.ano:
            return f"Notas do {self.ano} ano"
        return "Notas"


def get_comprovantes_directory(instance, filename):
    cpf = instance.inscricao.candidato.cpf
    inscricao_id = instance.inscricao_id
    return os.path.join("psct/comprovantes", cpf, str(inscricao_id), filename)


@reversion.register()
class Comprovante(models.Model):
    inscricao = models.ForeignKey(
        Inscricao,
        verbose_name="Inscrição",
        related_name="comprovantes",
        on_delete=models.PROTECT,
    )
    nome = models.CharField(max_length=255, verbose_name="Nome ou descrição do Arquivo")
    arquivo = DocumentFileField(
        verbose_name="Arquivo",
        upload_to=get_comprovantes_directory,
        size=6,
        format=["pdf", "png", "jpg", "jpeg", "tiff"],
    )
    data_criacao = models.DateTimeField(
        verbose_name="Data de criação", auto_now_add=True
    )
    data_atualizacao = models.DateTimeField(
        verbose_name="Data de atualização", auto_now=True
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Comprovante"
        verbose_name_plural = "Comprovantes"


class ComprovanteInscricao(models.Model):
    inscricao = models.OneToOneField(
        Inscricao,
        verbose_name="Inscrição",
        unique=True,
        related_name="comprovante",
        on_delete=models.PROTECT,
    )
    chave = models.CharField(verbose_name="Hash", max_length=255, unique=True)
    arquivo = models.FileField(verbose_name="Arquivo")
    data_criacao = models.DateTimeField(
        verbose_name="Data de Criação", auto_now_add=True
    )

    def __str__(self):
        return f"Comprovante emitido de {self.inscricao}"

    class Meta:
        verbose_name = "Comprovante de Inscrição"
        verbose_name_plural = "Comprovantes de Inscrição"


@reversion.register()
class CancelamentoInscricao(models.Model):
    inscricao = models.OneToOneField(
        Inscricao,
        verbose_name="Inscrição",
        related_name="cancelamento",
        on_delete=models.PROTECT,
    )
    usuario = models.ForeignKey(User, verbose_name="Usuário", on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(
        verbose_name="Data de criação", auto_now_add=True
    )

    def __str__(self):
        return f"Cancelamento de {self.inscricao}"

    class Meta:
        verbose_name = "Cancelamento de Inscrição"
        verbose_name_plural = "Cancelamentos de Inscrição"


class CursoEditalManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(qtd_vagas_total=Sum("modalidades__quantidade_vagas"))
        )


@reversion.register()
class CursoEdital(models.Model):
    edital = models.ForeignKey(Edital, verbose_name="Edital", on_delete=models.PROTECT)
    curso = models.ForeignKey(
        c_models.CursoSelecao, verbose_name="Curso", on_delete=models.PROTECT
    )

    objects = CursoEditalManager()

    def __str__(self):
        return f"Curso {self.curso} do edital {self.edital}"

    def clean(self):
        try:
            cursos = ProcessoInscricao.objects.get(edital=self.edital).cursos.all()
        except ProcessoInscricao.DoesNotExist:
            raise ValidationError(
                {
                    "edital": "Não existe processo de inscrição para o edital."
                }
            )

        if self.curso_id and self.curso not in cursos:
            raise ValidationError(
                {
                    "curso": "O curso não está presente no referido edital de processo de inscrição"
                }
            )

    class Meta:
        verbose_name = "Vaga dos cursos do processo de inscrição"
        verbose_name_plural = "Vagas dos cursos do processo de inscrição"
        constraints = (
            models.UniqueConstraint(fields=("edital", "curso"), name="cursoedital_unique"),
        )


@reversion.register()
class ModalidadeVagaCursoEdital(models.Model):
    curso_edital = models.ForeignKey(
        CursoEdital,
        verbose_name="Curso do Edital",
        related_name="modalidades",
        on_delete=models.PROTECT,
    )
    modalidade = models.ForeignKey(
        Modalidade, verbose_name="Modalidade", on_delete=models.PROTECT
    )
    quantidade_vagas = models.IntegerField(
        verbose_name="Quantidade de vagas", default=0
    )
    multiplicador = models.PositiveIntegerField(verbose_name="Multiplicador", default=1)

    def __str__(self):
        return "Curso {} do edital {} da modalidade {}".format(
            self.curso_edital.curso, self.curso_edital.edital, self.modalidade
        )

    class Meta:
        verbose_name = "Vaga por modalidade do curso do edital"
        verbose_name_plural = "Vagas por modalidade do curso do edital"
        unique_together = ("curso_edital", "modalidade")
        ordering = ("modalidade",)