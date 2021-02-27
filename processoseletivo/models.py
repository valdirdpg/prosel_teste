import csv
import io
import tempfile
from datetime import date, datetime
from enum import IntEnum

import reversion
import xlsxwriter
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.transaction import atomic
from django.db.utils import cached_property
from django.urls import reverse
from django.utils.decorators import method_decorator
from image_cropping import ImageRatioField

from base.cleaners import remove_simbolos_cpf
from base.history import HistoryMixin
from base.models import PessoaFisica
from base.utils import dias_entre
from noticias.models import PalavrasChave
from processoseletivo.choices import Status, StatusRecurso
from processoseletivo.templatetags.processoseletivo_tags import (
    confirmou_interesse_em_chamada,
)

GRUPO_CAMPI = "Administradores de Chamadas por Campi"
GRUPO_SISTEMICO = "Administradores Sistêmicos de Chamadas"
GRUPO_MEDICOS = "Médicos"
GRUPO_CAEST = "Operador CAEST"
SEXO_CHOICES = [("M", "Masculino"), ("F", "Feminino")]
SITUACAO_CHOICES = ((True, "Deferido"), (False, "Indeferido"))
CONFIRMACAO_INTERESSE_CHOICES = ((True, "Sim"), (False, "Não"))


def is_member(user, group_name):
    return user.groups.filter(name=group_name).exists()


def is_sistemico(user):
    return is_member(user, GRUPO_SISTEMICO)


def is_admin_campus(user):
    return is_member(user, GRUPO_CAMPI)


def existe_ciclo(arestas):

    if not arestas:
        return False

    fila = [arestas[0][0]]
    visitados = []
    while True:
        try:
            atual = fila.pop()
            if atual in visitados:
                return True
            destinos = [a[1] for a in arestas if a[0] == atual]
            fila.extend(destinos)
            visitados.append(atual)
        except IndexError:
            return False
    return False


class CampusEtapa:
    def __init__(self, campus, etapa):
        self.campus = campus
        self.etapa = etapa

    def vagas(self):
        chamadas = Chamada.objects.filter(etapa=self.etapa, curso__campus=self.campus)
        if chamadas:
            return chamadas.aggregate(Sum("vagas")).get("vagas__sum")
        else:
            return 0

    def matriculados(self):
        return Matricula.objects.filter(
            etapa=self.etapa, inscricao__curso__campus=self.campus
        ).count()

    def __getattr__(self, nome):
        return getattr(self.campus, nome)


class CursoEtapa:
    def __init__(self, curso, etapa):
        self.curso = curso
        self.etapa = etapa

    def vagas(self):
        chamadas = Chamada.objects.filter(etapa=self.etapa, curso=self.curso)
        if chamadas:
            return chamadas.aggregate(Sum("vagas")).get("vagas__sum")
        else:
            return 0

    def matriculados(self):
        return Matricula.objects.filter(
            etapa=self.etapa, inscricao__curso=self.curso
        ).count()

    def __getattr__(self, nome):
        return getattr(self.curso, nome)


class ProcessoSeletivo(models.Model, HistoryMixin):
    nome = models.CharField(verbose_name="Nome", max_length=255)
    sigla = models.CharField(verbose_name="Sigla", max_length=15)
    descricao = RichTextUploadingField(verbose_name="Descrição")
    imagem = models.ImageField(
        help_text="Ao concluir o preenchimento do formulário, clique em 'Salvar e continuar "
        "editando' para personalizar o tamanho da imagem. "
    )
    cropping = ImageRatioField(
        "imagem",
        "200x100",
        verbose_name="Imagem que será exibida",
        help_text="Clique e arraste para formar a área da imagem que será exibida no portal",
    )
    palavra_chave = models.ForeignKey(
        PalavrasChave, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Processo Seletivo"
        verbose_name_plural = "Processos Seletivos"
        ordering = ["sigla"]

    def __str__(self):
        return self.sigla

    def get_absolute_url(self):
        return reverse("processoseletivo", args=[str(self.id)])


class Edicao(models.Model):
    processo_seletivo = models.ForeignKey(
        ProcessoSeletivo, related_name="edicoes", on_delete=models.CASCADE
    )
    ano = models.IntegerField()
    semestre = models.IntegerField(blank=True, null=True)
    status = models.CharField(
        max_length=55, choices=[(x, x) for x in ["ABERTO", "FECHADO"]]
    )
    arquivo_resultado_csv = models.FileField(
        verbose_name="Resultado",
        null=True,
        blank=True,
        help_text="Arquivo CSV com o resultado",
        upload_to="processoseletivo/edicoes/csvs/",
    )
    arquivo_lista_espera_csv = models.FileField(
        verbose_name="Lista de espera",
        null=True,
        blank=True,
        help_text="Arquivo CSV com a lista de espera",
        upload_to="processoseletivo/edicoes/csvs/",
    )
    importado = models.BooleanField(default=False)
    nome = models.CharField(blank=True, null=True, max_length=50)
    descricao=models.CharField(blank=True, null=True, max_length=200)

    @property
    def pode_importar(self):
        return self.arquivo_lista_espera_csv and not self.importado

    def is_encerrada(self):
        return self.status != "ABERTO"

    def get_absolute_url(self):
        return reverse("etapas", args=(self.id,))

    def importar(self):
        if self.pode_importar:
            from . import loaders

            if self.arquivo_resultado_csv:
                loader = loaders.SisuLoader(
                    self.arquivo_resultado_csv.path,
                    encoding="UTF-8-sig",
                    delimiter=";",
                    initial_context=dict(edicao=self),
                )
                loader.run()

            skip_vagas = True if self.arquivo_resultado_csv else False

            loader = loaders.SisuLoader(
                self.arquivo_lista_espera_csv.path,
                encoding="UTF-8-sig",
                delimiter=";",
                initial_context=dict(edicao=self, skip_vagas=skip_vagas),
            )
            loader.run()

            self.definir_classificacoes()

            self.importado = True
            self.save()

    def definir_classificacoes(self):
        from cursos.models import CursoSelecao

        qs = CursoSelecao.objects.filter(inscricoes_mec__edicao=self).distinct()
        for index, curso in enumerate(qs, 1):
            desempenhos = []
            qs = Inscricao.objects.filter(
                edicao=self,
                curso=curso,
                modalidade_id=ModalidadeEnum.ampla_concorrencia,
            ).prefetch_related("desempenho")
            for inscricao in qs:
                desempenhos.append(inscricao.desempenho)

            def get_desempate(d):
                return (
                    d.nota_geral,
                    d.nota_na_redacao,
                    d.nota_em_linguas,
                    d.nota_em_matematica,
                    d.nota_em_ciencias_naturais,
                    d.nota_em_humanas,
                    dias_entre(
                        d.inscricao.candidato.pessoa.nascimento, datetime.today()
                    ),
                )

            desempenhos.sort(key=lambda d: get_desempate(d), reverse=True)

            for classificacao, d in enumerate(desempenhos, 1):
                Desempenho.objects.filter(
                    inscricao__candidato=d.inscricao.candidato,
                    inscricao__edicao=d.inscricao.edicao,
                    inscricao__curso=d.inscricao.curso,
                ).update(classificacao=classificacao)

    def __str__(self):
        to_string = []
        to_string.append(f"{self.processo_seletivo.sigla} {self.ano}")
        if self.semestre:
            to_string.append(f".{self.semestre}")
        if self.nome:
            to_string.append(f" - {self.nome}")
        return "".join(to_string)

    class Meta:
        verbose_name = "Edição"
        verbose_name_plural = "Edições de Processos Seletivos"

    @property
    def total_vagas(self):
        return self.vagas.count()

    @property
    def total_vagas_livres(self):
        if self.status == "ABERTO":
            return self.vagas_livres.count()
        else:
            return 0

    @property
    def vagas_livres(self):
        return self.vagas.filter(candidato__isnull=True)

    @property
    def is_psct_2017(self):
        return self.processo_seletivo.sigla == "PSCT" and self.ano == 2017

    def clean(self):
        super().clean()
        qs = Edicao.objects.filter(
            processo_seletivo=self.processo_seletivo,
            ano=self.ano,
            semestre=self.semestre,
            nome=self.nome,
        )
        if self.id:
            qs = qs.exclude(id=self.id)

        if qs.exists():
            raise ValidationError(
                "Já há uma edição de processo seletivo com as informações inseridas."
            )

    def get_modalidades_para_importacao(self):

        modalidades = set()

        def get_modalidades_from_file(filefield):
            with filefield.file as f:
                csvf = io.StringIO(f.read().decode("UTF-8-sig"), newline="\r")
                reader = csv.DictReader(csvf, delimiter=";")
                for line in reader:
                    modalidades.add(line["NO_MODALIDADE_CONCORRENCIA"])

        get_modalidades_from_file(self.arquivo_lista_espera_csv)

        if self.arquivo_resultado_csv:
            get_modalidades_from_file(self.arquivo_resultado_csv)

        modalidades = [
            m for m in modalidades if not Modalidade.objects.filter(nome=m).exists()
        ]
        modalidades = [
            m
            for m in modalidades
            if not ModalidadeVariavel.objects.filter(nome=m).exists()
        ]

        return sorted(modalidades)

    def exportar_dados(self):
        from cursos.models import CursoSelecao, Campus

        filename = tempfile.mktemp(suffix=".xls")
        workbook = xlsxwriter.Workbook(filename)
        for campus in Campus.objects.all().order_by("nome"):

            if (
                not Inscricao.objects.filter(edicao=self, curso__campus=campus)
                .distinct()
                .exists()
            ):
                continue

            worksheet = workbook.add_worksheet(campus.nome[:30])
            counter = 0
            cursos = CursoSelecao.objects.filter(
                inscricoes_mec__edicao=self, campus=campus
            ).distinct()
            for curso in cursos:
                for modalidade in Modalidade.objects.all():

                    qs = (
                        Inscricao.objects.filter(
                            edicao=self, curso=curso, modalidade=modalidade
                        )
                        .prefetch_related("desempenho")
                        .distinct()
                    )

                    if not qs.exists():
                        continue

                    worksheet.write(counter, 0, str(curso))
                    worksheet.write(counter, 1, str(modalidade))
                    counter += 1
                    worksheet.write(counter, 0, "Nome")
                    worksheet.write(counter, 1, "Classificação")
                    worksheet.write(counter, 2, "Nota Geral")
                    worksheet.write(counter, 3, "Nota em Línguas")
                    worksheet.write(counter, 4, "Nota em Matemática")
                    worksheet.write(counter, 5, "Nota em Ciências")
                    worksheet.write(counter, 6, "Nota em Humanas")

                    counter += 1

                    inscricoes = sorted(
                        [i for i in qs], key=lambda i: i.desempenho.classificacao
                    )

                    for inscricao in inscricoes:
                        desempenho = inscricao.desempenho
                        worksheet.write(counter, 0, inscricao.candidato.pessoa.nome)
                        worksheet.write(counter, 1, desempenho.classificacao)
                        worksheet.write(counter, 2, desempenho.nota_geral)
                        worksheet.write(counter, 3, desempenho.nota_em_linguas)
                        worksheet.write(counter, 4, desempenho.nota_em_matematica)
                        worksheet.write(
                            counter, 5, desempenho.nota_em_ciencias_naturais
                        )
                        worksheet.write(counter, 6, desempenho.nota_em_humanas)

                        counter += 1
                    counter += 2

        workbook.close()
        return filename


@reversion.register()
class Modalidade(models.Model):
    nome = models.CharField(max_length=255, unique=True)
    resumo = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.resumo if self.resumo else self.nome

    @classmethod
    def ids_cota_pcd(cls):
        return [
            ModalidadeEnum.renda_inferior_pcd,
            ModalidadeEnum.renda_inferior_cota_racial_pcd,
            ModalidadeEnum.cota_racial_pcd,
            ModalidadeEnum.escola_publica_pcd,
            ModalidadeEnum.deficientes,
        ]

    @classmethod
    def ids_cota_racial(cls):
        return [
            ModalidadeEnum.cota_racial,
            ModalidadeEnum.renda_inferior_cota_racial,
            ModalidadeEnum.cota_racial_pcd,
            ModalidadeEnum.renda_inferior_cota_racial_pcd,
        ]

    @classmethod
    def ids_cota_renda(cls):
        return [
            ModalidadeEnum.renda_inferior,
            ModalidadeEnum.renda_inferior_cota_racial,
            ModalidadeEnum.renda_inferior_pcd,
            ModalidadeEnum.renda_inferior_cota_racial_pcd,
        ]

    def is_ampla_concorrencia(self):
        return self.pk == ModalidadeEnum.ampla_concorrencia

    def is_escola_publica(self):
        return self.pk not in [
            ModalidadeEnum.ampla_concorrencia,
            ModalidadeEnum.deficientes,
        ]

    def is_cota_pcd(self):
        return self.pk in self.ids_cota_pcd()

    def is_cota_racial(self):
        return self.pk in self.ids_cota_racial()

    def is_cota_renda(self):
        return self.pk in self.ids_cota_renda()

    def is_cota_rural(self):
        return self.pk == ModalidadeEnum.rurais


class ModalidadeVariavel(models.Model):
    modalidade = models.ForeignKey(
        Modalidade, verbose_name="Modalidade de cota primária", on_delete=models.CASCADE
    )
    nome = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nome


@reversion.register()
class Etapa(models.Model):
    edicao = models.ForeignKey(Edicao, verbose_name="Edição", on_delete=models.CASCADE)
    numero = models.IntegerField("Número da Etapa")
    campus = models.ForeignKey(
        "cursos.Campus",
        verbose_name="Campus",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    multiplicador = models.IntegerField(
        verbose_name="Número de convocados",
        help_text="Quantidade de candidatos convocados por cada vaga remanescente",
    )
    publica = models.BooleanField(default=False, verbose_name="Publicar chamada")
    encerrada = models.BooleanField(default=False)

    class Meta:
        unique_together = ("edicao", "numero", "campus")

    class Error(Exception):
        pass

    class EncerrarEtapaError(ValidationError):
        pass

    def conf_interesse_nao_avaliadas(self):
        qs = ConfirmacaoInteresse.objects.filter(etapa=self).exclude(
            analisedocumental__isnull=False
        )
        return qs

    def pode_encerrar(self):
        return (
            True
            if not self.analise_documentacao_gerenciada
            else not self.conf_interesse_nao_avaliadas().exists()
        )

    def pode_reabrir(self):
        if self.id:
            ultima_etapa = self.get_ultima_etapa()
            return (
                ultima_etapa and ultima_etapa.id == self.id and ultima_etapa.encerrada
            )
        return False

    @classmethod
    def possui_etapa_campus(self, edicao):
        if edicao:
            return Etapa.objects.filter(edicao=edicao, campus__isnull=False).exists()
        return False

    def get_cronograma_convocacao(self, evento):
        return self.cronogramas_convocacao.filter(evento=evento).last()

    def _verificar_periodo(self, evento):
        periodo = self.cronogramas_convocacao.filter(evento=evento).last()
        return periodo and periodo.gerenciavel

    @cached_property
    def manifestacao_interesse_gerenciada(self):
        return self._verificar_periodo("INTERESSE")

    @cached_property
    def analise_documentacao_gerenciada(self):
        return self._verificar_periodo("ANALISE")

    @method_decorator(atomic)
    def gerar_chamadas(self):
        from cursos.models import CursoSelecao

        if not self.chamadas.all().exists():

            if self.campus:
                filters = {"campus": self.campus}
            else:
                filters = {}

            cursos = CursoSelecao.objects.filter(
                vaga__edicao=self.edicao, vaga__candidato__isnull=True, **filters
            ).distinct()
            for curso in cursos:
                vagas = Vaga.objects.select_related("modalidade").filter(
                    edicao=self.edicao, curso=curso, candidato__isnull=True
                )
                for vaga in vagas:
                    vaga.buscar_nova_modalidade()

                modalidades = vagas.values_list("modalidade", flat=True).distinct()
                for modalidade_id in modalidades:
                    modalidade = Modalidade.objects.get(id=modalidade_id)
                    chamada = Chamada.objects.create(
                        curso=curso,
                        modalidade=modalidade,
                        etapa=self,
                        multiplicador=self.multiplicador,
                    )
                    chamada.adicionar_inscricoes()

    def get_absolute_url(self):
        return reverse("edicao_etapa", args=(self.edicao_id, self.pk))

    @property
    def nome(self):
        if self.is_resultado:
            numero = "de Resultado"
        else:
            numero = self.numero

        if not self.campus:
            return f"Etapa {numero}"
        return f"Etapa {numero} - Campus {self.campus}"

    @property
    def data_inicio(self):
        return self.get_cronograma_convocacao("INTERESSE").inicio

    def __str__(self):
        return f"{self.edicao} - {self.nome}"

    def clean(self):
        if self.edicao_id:
            if not self.edicao.importado:
                raise ValidationError(
                    {"edicao": "Esta edição não possui dados de candidatos importados."}
                )

            if not self.id:
                ultima_etapa = self.get_ultima_etapa()
                if ultima_etapa and not ultima_etapa.encerrada:
                    raise ValidationError(
                        "Existe outra etapa aberta para esta edição. Você deve encerrá-la antes de continuar."
                    )

                if not self.campus and self.possui_etapa_campus(self.edicao):
                    raise ValidationError(
                        "Você não pode criar uma etapa sistêmica, pois já existe etapa de campus criada para esta edição."
                    )

            numero = self.get_numero()

            if self.multiplicador != 1 and numero == 0 and not self.campus:
                raise ValidationError(
                    "A etapa de resultado não pode ter multiplicador diferente de 1"
                )

        if self.encerrada and not self.pode_encerrar():
            msg_error = "Há confirmações de interesses que não foram analisadas:"
            for ci in self.conf_interesse_nao_avaliadas():
                msg_error += " (*) {} <Modalidade: {}, Curso: {}, {}>".format(
                    ci.inscricao.candidato,
                    ci.inscricao.modalidade,
                    ci.inscricao.curso.nome,
                    ci.inscricao.curso.campus,
                )
            raise ValidationError(msg_error)

        super().clean()

    def get_numero(self):
        if self.numero is None:
            ultima_etapa = self.get_ultima_etapa()
            if not ultima_etapa:
                if not (
                    self.edicao.arquivo_resultado_csv
                    or self.edicao.arquivo_lista_espera_csv
                ):
                    return 0
                elif self.edicao.arquivo_resultado_csv:
                    return 0
                else:
                    return 1
            else:
                return ultima_etapa.numero + 1
        else:
            return self.numero

    def get_ultima_etapa(self):
        queryset = Q(campus=self.campus) | Q(campus=None)
        return Etapa.objects.filter(queryset, edicao=self.edicao).last()

    @property
    def is_resultado(self):
        return self.numero == 0

    @property
    def label(self):
        if self.is_resultado:
            return "Chamada do Resultado"
        return f"{self.numero}ª Chamada"

    def save(self, *args, **kwargs):
        self.numero = self.get_numero()
        super().save(*args, **kwargs)

    def exportar(self, matriculados=False):
        from cursos.models import Campus

        filename = tempfile.mktemp(prefix="lista", suffix=".xlsx")
        workbook = xlsxwriter.Workbook(filename)

        if self.campus:
            qs = [self.campus]
        else:
            if not matriculados:
                qs = Campus.objects.filter(
                    cursonocampus__chamada__isnull=False,
                    cursonocampus__chamada__etapa=self,
                ).distinct()
            else:
                qs = Campus.objects.filter(
                    cursonocampus__chamada__isnull=False,
                    cursonocampus__chamada__etapa=self,
                    cursonocampus__inscricoes_mec__matricula__isnull=False,
                    cursonocampus__inscricoes_mec__matricula__etapa=self,
                ).distinct()

        for campus in qs:
            worksheet = workbook.add_worksheet(campus.nome[:30])
            counter = 0
            chamadas = Chamada.objects.filter(
                etapa=self, curso__campus=campus
            ).order_by("curso", "modalidade")

            for chamada in chamadas:
                worksheet.write(counter, 0, str(chamada.curso))
                worksheet.write(counter, 1, str(chamada.modalidade))
                counter += 1
                worksheet.write(counter, 0, "Nome")
                worksheet.write(counter, 1, "Classificação")
                worksheet.write(counter, 2, "E-mail")
                worksheet.write(counter, 3, "Telefone")
                worksheet.write(counter, 4, "Telefone")
                counter += 1

                if not matriculados:
                    qs = chamada.inscricoes.all()
                else:
                    qs = chamada.inscricoes.filter(matricula__isnull=False)

                for inscricao in qs:
                    candidato = inscricao.candidato
                    worksheet.write(counter, 0, candidato.pessoa.nome)
                    worksheet.write(counter, 1, inscricao.desempenho.classificacao)
                    worksheet.write(counter, 2, candidato.pessoa.email)
                    worksheet.write(counter, 3, candidato.pessoa.telefone)
                    worksheet.write(counter, 4, candidato.pessoa.telefone2)
                    counter += 1
                counter += 2

        workbook.close()
        return filename

    def reabrir(self):
        with transaction.atomic():
            self.desmatricular()
            Resultado.objects.filter(etapa=self).delete()
            Matricula.objects.filter(etapa=self).delete()
            self.encerrada = False
            self.save()

    def desmatricular(self):
        resultados = Resultado.objects.filter(etapa=self)
        for resultado in resultados:
            Vaga.objects.filter(
                edicao=self.edicao,
                candidato=resultado.inscricao.candidato,
                curso=resultado.inscricao.curso,
                modalidade=resultado.inscricao.modalidade,
            ).update(candidato=None)

    def mover_analise_e_confirmacao(self, inscricao_cota, inscricao_ampla):
        if ConfirmacaoInteresse.objects.filter(
            inscricao=inscricao_ampla, etapa=self
        ).exists():

            raise ConfirmacaoInteresse.Error(
                "Confirmação de interesse já existe na ampla concorrência."
            )

        confirmacao_interesse = ConfirmacaoInteresse.objects.filter(
            inscricao=inscricao_cota, etapa=self
        ).last()

        confirmacao_interesse.inscricao = inscricao_ampla
        confirmacao_interesse.save()

    def encerrar(self):

        with transaction.atomic():

            if self.encerrada:
                raise self.Error("Etapa já encerrada")

            if self.get_numero() > 0:

                candidatos_em_duas_chamadas = (
                    Candidato.objects.filter(inscricoes__chamada__etapa=self)
                    .annotate(n_inscricoes=Count("inscricoes"))
                    .filter(n_inscricoes=2)
                )

                for candidato in candidatos_em_duas_chamadas:
                    inscricao_cota = (
                        candidato.inscricoes.filter(chamada__etapa=self)
                        .exclude(modalidade__pk=ModalidadeEnum.ampla_concorrencia)
                        .last()
                    )

                    if inscricao_cota.get_situacao().get_mensagem() in [
                        "Apto(a)",
                        "Documentação atende aos requisitos",
                    ]:

                        chamada_cota, qtd_vagas = (
                            inscricao_cota.chamada,
                            inscricao_cota.chamada.vagas,
                        )

                        inscricoes_da_cota = Inscricao.objects.filter(
                            curso=chamada_cota.curso,
                            modalidade=inscricao_cota.modalidade,
                            edicao=inscricao_cota.edicao,
                            chamada=chamada_cota,
                        ).order_by("desempenho__classificacao")

                        inscricoes_aptas_cota = []
                        for inscricao in inscricoes_da_cota:
                            if inscricao.get_situacao().get_mensagem() in [
                                "Apto(a)",
                                "Documentação atende aos requisitos",
                            ]:
                                inscricoes_aptas_cota.append(inscricao)

                        if inscricoes_aptas_cota.index(inscricao_cota) > qtd_vagas - 1:

                            inscricao_ampla = (
                                candidato.inscricoes.filter(
                                    chamada__etapa=self,
                                    modalidade__pk=ModalidadeEnum.ampla_concorrencia,
                                )
                                .order_by("modalidade_id", "chamada__data")
                                .first()
                            )

                            inscricoes_da_ampla = Inscricao.objects.filter(
                                curso=chamada_cota.curso,
                                modalidade__pk=ModalidadeEnum.ampla_concorrencia,
                                edicao=inscricao_cota.edicao,
                                chamada=inscricao_ampla.chamada,
                            ).order_by("desempenho__classificacao")

                            inscricoes_aptas_ampla = []
                            for inscricao in inscricoes_da_ampla:
                                if inscricao.get_situacao().get_mensagem() in [
                                    "Apto(a)",
                                    "Documentação atende aos requisitos",
                                ]:
                                    inscricoes_aptas_ampla.append(inscricao)
                            inscricoes_aptas_ampla.append(inscricao_ampla)

                            ins_ids = [i.id for i in inscricoes_aptas_ampla]
                            inscricoes_aptas_ampla = list(
                                Inscricao.objects.filter(id__in=ins_ids).order_by(
                                    "desempenho__classificacao"
                                )
                            )

                            if (
                                inscricoes_aptas_ampla.index(inscricao_ampla)
                                < inscricao_ampla.chamada.vagas
                            ):
                                self.mover_analise_e_confirmacao(
                                    inscricao_cota, inscricao_ampla
                                )

            for chamada in self.chamadas.all():

                vagas = Vaga.objects.filter(
                    modalidade=chamada.modalidade,
                    edicao=chamada.etapa.edicao,
                    curso=chamada.curso,
                    candidato__isnull=True,
                ).count()
                vagas_reais = vagas

                vagas_chamada = vagas * chamada.multiplicador
                inscricoes = chamada.inscricoes.all()[:vagas_chamada]

                vagas_preenchidas = 0

                for inscricao in inscricoes:
                    analise = AnaliseDocumental.objects.filter(
                        confirmacao_interesse__inscricao=inscricao
                    ).first()

                    if self.analise_documentacao_gerenciada:
                        if vagas_preenchidas < vagas:
                            status, observacao = self._verificar_status(
                                analise,
                                Status.DEFERIDO.value,
                                "CANDIDATO APTO A REALIZAR MATRÍCULA",
                            )
                        else:
                            status, observacao = self._verificar_status(
                                analise,
                                Status.EXCEDENTE.value,
                                "CANDIDATO NA LISTA DE ESPERA",
                            )
                    elif ConfirmacaoInteresse.objects.filter(
                        inscricao=inscricao
                    ).exists():
                        if vagas_preenchidas < vagas:
                            status = Status.DEFERIDO.value
                            observacao = "CANDIDATO APTO A REALIZAR MATRÍCULA"
                        else:
                            status = Status.EXCEDENTE.value
                            observacao = "CANDIDATO NA LISTA DE ESPERA"
                    else:
                        status = Status.INDEFERIDO.value
                        observacao = "DOCUMENTAÇÃO NÃO ENTREGUE"

                    if status == Status.DEFERIDO.value:
                        inscricao.matricular(self)

                    if status in [Status.DEFERIDO.value]:
                        vagas_preenchidas += 1

                    if observacao != "DOCUMENTAÇÃO NÃO ENTREGUE":
                        Resultado.objects.create(
                            etapa=self,
                            inscricao=inscricao,
                            status=status,
                            observacao=observacao,
                        )

            erros = []
            inscricoes_cotas_etapa_atual = Inscricao.objects.filter(
                chamada__etapa=self, confirmacaointeresse__isnull=False
            ).exclude(modalidade__pk=ModalidadeEnum.ampla_concorrencia.value)
            for inscricao in inscricoes_cotas_etapa_atual:
                tipos_analise = inscricao.modalidade.tipos_analise
                avaliacoes = AvaliacaoDocumental.objects.filter(
                    analise_documental__confirmacao_interesse__inscricao=inscricao
                )
                if not tipos_analise.count() == avaliacoes.count():
                    erros.append(
                        f"A inscricão do candidato {inscricao.candidato} possui quantidade de "
                        f"avaliações diferente dos tipos de análise da modalidade"
                    )

                for avaliacao in avaliacoes:
                    if avaliacao.tipo_analise not in tipos_analise.all():
                        erros.append(
                            f"A inscrição do candidato {inscricao.candidato} possui avaliação "
                            f"inexistente nos tipos de análise da cota"
                        )

            if erros:
                raise Etapa.EncerrarEtapaError(erros)

            self.encerrada = True
            self.save()

    def _verificar_status(self, analise, status, observacao):
        if analise:
            if analise.situacao_final:
                return status, observacao
            else:
                recurso = Recurso.objects.filter(analise_documental=analise).first()
                if recurso:
                    if recurso.status_recurso == Status.DEFERIDO.value:
                        return status, observacao
                    else:
                        return (
                            Status.INDEFERIDO.value,
                            "RECURSO INDEFERIDO - " + recurso.justificativa.upper(),
                        )
                else:
                    return (
                        Status.INDEFERIDO.value,
                        "DOCUMENTAÇÃO INVÁLIDA - " + analise.observacao.upper(),
                    )
        else:
            return Status.INDEFERIDO.value, "DOCUMENTAÇÃO NÃO ENTREGUE"

    def estah_em_periodo_analise(self):
        analise = self.get_cronograma_convocacao("ANALISE")
        return analise and analise.gerenciavel and analise.is_vigente()


@reversion.register()
class Chamada(models.Model):
    etapa = models.ForeignKey(Etapa, related_name="chamadas", on_delete=models.CASCADE)
    modalidade = models.ForeignKey(Modalidade, on_delete=models.CASCADE)
    curso = models.ForeignKey("cursos.CursoSelecao", on_delete=models.CASCADE)
    data = models.DateField(auto_now_add=True)
    multiplicador = models.IntegerField(verbose_name="Quantidade de convocações")
    vagas = models.IntegerField(default=0, null=True, blank=True)

    def adicionar_inscricoes(self):
        self.inscricoes.clear()
        vagas = Vaga.objects.filter(
            modalidade=self.modalidade,
            edicao=self.etapa.edicao,
            curso=self.curso,
            candidato__isnull=True,
        ).count()

        self.vagas = vagas
        self.save()

        query = {
            "edicao": self.etapa.edicao,
            "curso": self.curso,
            "modalidade": self.modalidade,
            "chamada": None,
        }

        vagas *= self.multiplicador
        qs = Inscricao.objects.filter(**query).exclude(
            candidato__inscricoes__matricula__etapa__edicao=self.etapa.edicao
        )[:vagas]
        self.inscricoes.add(*qs)
        self.criar_usuarios_pendentes()

    def criar_usuarios_pendentes(self):
        qs = self.inscricoes.filter(candidato__pessoa__user__isnull=True)

        for inscricao in qs:
            pessoa = inscricao.candidato.pessoa
            first_name, *ignore, last_name = pessoa.nome.split()

            group_candidatos = Group.objects.get(name="Candidatos")
            qs = User.objects.filter(username=remove_simbolos_cpf(pessoa.cpf))
            if qs.exists():
                pessoa.user = qs.first()
                pessoa.user.groups.add(group_candidatos)
                if pessoa.user.email != pessoa.email:
                    pessoa.user.email = pessoa.email
                    pessoa.user.save()
                pessoa.save()
            else:
                user = User(
                    username=remove_simbolos_cpf(pessoa.cpf),
                    email=pessoa.email,
                    first_name=first_name,
                    last_name=last_name,
                )
                user.set_password(User.objects.make_random_password(length=24))
                user.save()
                user.groups.add(group_candidatos)
                pessoa.user = user
                pessoa.save()

    def get_absolute_url(self):
        return reverse(
            "chamadas", args=(self.etapa.id, self.curso.campus.id, self.curso.id)
        )

    def __str__(self):
        return "{}. Modalidade {} - {} / {}".format(
            self.curso, self.modalidade, self.data, self.etapa
        )

    @property
    def editavel(self):
        if self.candidatos.all():
            return False
        return True

    def clean(self):
        super().clean()
        if Chamada.objects.filter(
            etapa=self.etapa, modalidade=self.modalidade, curso=self.curso
        ).exclude(id=self.id):
            raise ValidationError("Essa chamada já foi inserida")
        if self.etapa.encerrada:
            raise ValidationError("A etapa já foi encerrada!")

        if self.etapa.is_resultado and self.multiplicador != 1:
            raise ValidationError(
                "A chamada de resultado não pode ter multiplicado maior que 1"
            )

    def get_confirmacoes_interesse(self):
        return ConfirmacaoInteresse.objects.filter(inscricao__chamada=self)

    def get_analises_documentais(self):
        return AnaliseDocumental.objects.filter(
            confirmacao_interesse__inscricao__chamada=self
        )


class Candidato(models.Model):
    pessoa = models.OneToOneField(
        PessoaFisica,
        verbose_name="Pessoa Física",
        related_name="candidato_ps",
        on_delete=models.PROTECT,
    )

    def get_classificacao_em_edicao(self, edicao, curso):
        desempenho = Desempenho.objects.filter(
            inscricao__edicao=edicao, inscricao__candidato=self, inscricao__curso=curso
        ).first()
        return desempenho.classificacao

    def __str__(self):
        return self.pessoa.nome.upper()

    class Meta:
        ordering = ("pessoa__nome",)


class Desempenho(models.Model):
    inscricao = models.OneToOneField(
        "processoseletivo.Inscricao", verbose_name="Inscrição", on_delete=models.CASCADE
    )
    nota_em_linguas = models.DecimalField(
        max_digits=6, decimal_places=2, verbose_name="Nota em Línguas"
    )
    nota_em_humanas = models.DecimalField(
        max_digits=6, decimal_places=2, verbose_name="Nota em Ciências Humanas"
    )
    nota_em_ciencias_naturais = models.DecimalField(
        max_digits=6, decimal_places=2, verbose_name="Nota em Ciências Naturais"
    )
    nota_em_matematica = models.DecimalField(
        max_digits=6, decimal_places=2, verbose_name="Nota em matemática"
    )
    nota_na_redacao = models.DecimalField(
        max_digits=6, decimal_places=2, verbose_name="Nota na redação"
    )
    nota_geral = models.DecimalField(
        max_digits=6, decimal_places=2, verbose_name="Nota final"
    )
    classificacao = models.IntegerField()

    @property
    def nome_candidato(self):
        return self.inscricao.candidato.pessoa.nome

    def __str__(self):
        return "{0.nome_candidato} {0.nota_geral} {0.classificacao}".format(self)


class Inscricao(models.Model):

    candidato = models.ForeignKey(
        Candidato, related_name="inscricoes", on_delete=models.CASCADE
    )
    curso = models.ForeignKey(
        "cursos.CursoSelecao", related_name="inscricoes_mec", on_delete=models.CASCADE
    )
    modalidade = models.ForeignKey(Modalidade, on_delete=models.CASCADE)
    edicao = models.ForeignKey(Edicao, on_delete=models.CASCADE)
    chamada = models.ForeignKey(
        Chamada,
        verbose_name="Chamada",
        on_delete=models.SET_NULL,
        related_name="inscricoes",
        null=True,
        blank=True,
    )

    def __str__(self):
        return "{0.candidato} - {0.curso.nome} - {0.curso.turno} - {0.curso.campus} - {0.modalidade} - {0.edicao}".format(
            self
        )

    class Meta:
        verbose_name = "Inscrição"
        verbose_name_plural = "Inscrições"
        ordering = ("desempenho__classificacao",)

    def matricular(self, etapa):
        if Matricula.objects.filter(
            inscricao__candidato=self.candidato, etapa__edicao=etapa.edicao
        ).exists():
            raise Matricula.Error("Candidato já matriculado")
        else:
            vaga = Vaga.objects.filter(
                curso=self.curso,
                edicao=self.edicao,
                modalidade=self.modalidade,
                candidato__isnull=True,
            ).first()
            if vaga:
                vaga.candidato = self.candidato
                vaga.save()
                Matricula.objects.create(inscricao=self, etapa=etapa)
            else:
                raise Matricula.Error("Sem vagas disponíveis")

    def cancelar_matricula(self, etapa):
        matricula = Matricula.objects.filter(inscricao=self, etapa=etapa).first()
        if matricula:
            if matricula.inscricao == self:
                matricula.delete()
                Vaga.objects.filter(candidato=self.candidato).update(candidato=None)
            else:
                raise Matricula.Error("Aluno matriculado por outra inscrição")
        else:
            raise Matricula.Error("Candidato não está matriculado")

    def confirmar_interesse(self, etapa):
        confirmacao = ConfirmacaoInteresse(inscricao=self, etapa=etapa)
        try:
            confirmacao.clean()
            confirmacao.save()
        except ValidationError as v:
            raise ConfirmacaoInteresse.Error(v.message)

    def cancelar_interesse(self, etapa):
        confirmacao_interesse = ConfirmacaoInteresse.objects.filter(
            inscricao=self
        ).first()
        if confirmacao_interesse and confirmacao_interesse.pode_apagar():
            confirmacao_interesse.delete()
        else:
            raise ConfirmacaoInteresse.Error(
                "Não é possível cancelar interesse, pois o período de Confirmação de Interesse não está vigente."
            )

    def status_documentacao(self):
        if not ConfirmacaoInteresse.objects.filter(inscricao=self).exists():
            return None

        analise = AnaliseDocumental.objects.filter(
            confirmacao_interesse__inscricao=self
        ).first()
        if analise:
            return analise.situacao_final
        else:
            return "Não Avaliado"

    def status_recurso(self):
        if not ConfirmacaoInteresse.objects.filter(inscricao=self).exists():
            return None

        recurso = Recurso.objects.filter(
            analise_documental__confirmacao_interesse__inscricao=self
        ).first()
        if recurso:
            return recurso.status_recurso
        else:
            return "Não houve"

    def get_matriculado_em_chamada(self, etapa):
        return (
            Matricula.objects.select_related("inscricao")
            .filter(inscricao=self, etapa=etapa)
            .exists()
        )

    def get_inscricao_outra_chamada(self, etapa):
        candidato = self.candidato
        outra_inscricao = (
            candidato.inscricoes.filter(chamada__etapa=etapa)
            .exclude(pk=self.id)
            .first()
        )

        return outra_inscricao

    def get_situacao_matricula_outra_chamada(self, etapa):
        outra_inscricao = self.get_inscricao_outra_chamada(etapa)

        if outra_inscricao:
            matricula = Matricula.objects.filter(inscricao=outra_inscricao)
            if matricula.exists():
                if outra_inscricao.modalidade.is_ampla_concorrencia():
                    return "Matriculado(a) na lista geral"
                else:
                    return "Matriculado(a) em Cota"
        return None

    def get_situacao_matricula_em_chamada(self, etapa):
        situacao = self.get_situacao_matricula_outra_chamada(etapa)
        if situacao:
            return situacao

        if not etapa.encerrada:
            return "-"
        situacao = "Não compareceu"
        if self.get_matriculado_em_chamada(etapa):
            situacao = "Matriculado(a)"
        elif etapa.analise_documentacao_gerenciada:
            st_documentacao = self.status_documentacao()
            if st_documentacao is True or self.status_recurso() == "DEFERIDO":
                situacao = "Lista de Espera"
            elif st_documentacao is False:
                situacao = "Doc. Indeferida"
        elif hasattr(self, "confirmacaointeresse"):
            situacao = "Lista de Espera"

        if situacao == "Não compareceu":
            outra_inscricao = self.get_inscricao_outra_chamada(etapa)
            if outra_inscricao:
                matricula = Matricula.objects.filter(inscricao=self)
                if (
                    outra_inscricao.get_situacao().get_mensagem()
                    in ["Apto(a)", "Documentação atende aos requisitos"]
                    and not matricula.exists()
                ):
                    situacao = "Lista de Espera"
                    # lista de espera em outra chamada

        return situacao

    def get_situacao(self):
        """
        Retorna a situação atual.
        Convocado: Assim que a etapa é publicada
        Não compareceu: Quando a etapa encerrou e o candidato não confirmou interesse
        Aguardando avaliação: Quando o candidato confirmou interesse + análise é gerenciada no site
        Situação da Análise[deferido/indeferido]: Quando foi feita a análise dos documentos
        Apto: Quando o recurso foi aceito ou confirmou interesse e a análise não é gerenciada
        :return: SituacaoInscricao
        """
        etapa = self.chamada.etapa
        if self.get_matriculado_em_chamada(etapa):
            return SituacaoMatriculado()

        matriculado_chamada_diferente = self.get_situacao_matricula_outra_chamada(etapa)
        if matriculado_chamada_diferente:
            return SituacaoMatriculado(mensagem=matriculado_chamada_diferente)

        cronograma = etapa.get_cronograma_convocacao("ANALISE")
        if cronograma and cronograma.is_encerrado():
            confirmou_interesse = confirmou_interesse_em_chamada(self, etapa)
            if confirmou_interesse:
                if etapa.analise_documentacao_gerenciada:
                    analise = AnaliseDocumental.objects.filter(
                        confirmacao_interesse__inscricao=self
                    ).first()
                    if analise:
                        recurso = Recurso.objects.filter(
                            analise_documental=analise
                        ).first()
                        if (
                            recurso
                            and recurso.status_recurso == StatusRecurso.DEFERIDO.value
                        ):
                            return SituacaoApto()
                        return SituacaoAnaliseDocumental(
                            analise.situacao_final, analise.observacao
                        )
                    return SituacaoAguardandoAvaliacao()
                else:
                    return SituacaoApto()
            else:
                inscricao_outra_chamada = self.get_inscricao_outra_chamada(etapa)
                if inscricao_outra_chamada and confirmou_interesse_em_chamada(
                    inscricao_outra_chamada, etapa
                ):
                    return SituacaoNaoDefinida("Avaliado(a) em outra cota")
            if etapa.encerrada:
                return SituacaoNaoCompareceu()
        if etapa.publica:
            return SituacaoConvocado()
        return SituacaoNaoDefinida()


class SituacaoInscricao:
    def __str__(self):
        return self.get_mensagem()

    def get_mensagem(self):
        raise TypeError()

    def get_css_class(self):
        raise TypeError()


class SituacaoNaoDefinida(SituacaoInscricao):
    def __init__(self, mensagem="Não definida"):
        self.mensagem = mensagem

    def get_mensagem(self):
        return f"{self.mensagem}"

    def get_css_class(self):
        return "disabled"


class SituacaoConvocado(SituacaoInscricao):
    def get_mensagem(self):
        return "Convocado(a)"

    def get_css_class(self):
        return "success"


class SituacaoApto(SituacaoInscricao):
    def get_mensagem(self):
        return "Apto(a)"

    def get_css_class(self):
        return "success"


class SituacaoAguardandoAvaliacao(SituacaoInscricao):
    def get_mensagem(self):
        return "Aguardando avaliação de documentos"

    def get_css_class(self):
        return "pendente"


class SituacaoAnaliseDocumental(SituacaoInscricao):
    def __init__(self, situacao, observacoes=""):
        self.situacao = situacao
        self.observacoes = observacoes

    def get_mensagem(self):
        if self.situacao:
            return "Documentação atende aos requisitos"
        else:
            return "Documentação indeferida"

    def get_css_class(self):
        if self.situacao:
            return "deferido"
        else:
            return "indeferido"

    def get_observacoes(self):
        return self.observacoes


class SituacaoNaoCompareceu(SituacaoInscricao):
    def get_mensagem(self):
        return "Não compareceu"

    def get_css_class(self):
        return "indeferido"


class SituacaoMatriculado(SituacaoInscricao):
    def __init__(self, mensagem="Matriculado(a)"):
        self.mensagem = mensagem

    def get_mensagem(self):
        return f"{self.mensagem}"

    def get_css_class(self):
        return "deferido"


class ConfirmacaoInteresse(models.Model):
    class Error(Exception):
        pass

    inscricao = models.OneToOneField(Inscricao, on_delete=models.CASCADE)
    etapa = models.ForeignKey(
        Etapa, related_name="confirmacoes_interesse", on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.inscricao)

    class Meta:
        verbose_name = "Confirmação de Interesse"
        verbose_name_plural = "Confirmações de Interesse"
        ordering = ["inscricao__candidato"]

    def pode_apagar(self):
        from editais.models import PeriodoConvocacao

        periodo = PeriodoConvocacao.objects.get(etapa=self.etapa, evento="ANALISE")
        if periodo and not periodo.is_vigente():
            return False
        return True

    def clean(self):
        super().clean()
        from editais.models import PeriodoConvocacao

        gerenciar_interesse = None

        if self.etapa_id:
            periodo_interesse = PeriodoConvocacao.objects.filter(
                etapa=self.etapa, evento="INTERESSE"
            ).last()
            gerenciar_interese = periodo_interesse and periodo_interesse.gerenciavel
            periodo_analise = PeriodoConvocacao.objects.filter(
                etapa=self.etapa, evento="ANALISE"
            ).last()

            if self.etapa.encerrada:
                raise ValidationError("Etapa encerrada.")

            """
            [RN] A confirmação de Interesse só pode ser efetuada no período de vigência do 
            cronograma "Análise de Documentação"
            """
            if periodo_analise and not periodo_analise.is_vigente():
                raise ValidationError(
                    "A confirmação de interesse do candidato deve ser feita durante o período "
                    "de Análise de Documentação."
                )

        if self.inscricao_id:
            """
            [RN] O candidato não pode ter mais de 1 manifesto de interesse em uma mesma etapa
            """
            if (
                self.etapa_id
                and self.__class__.objects.filter(
                    inscricao__candidato=self.inscricao.candidato, etapa=self.etapa
                )
                .exclude(inscricao=self.inscricao)
                .exists()
            ):
                raise ValidationError(
                    "Interesse do candidato já registrado nesta etapa em outra modalidade."
                )

            """
            [RN] O candidato deve ter atualizado seus dados há X dias.
            """

            if not gerenciar_interese:
                return

            if not self.inscricao.candidato.pessoa.is_atualizado_recentemente():
                raise ValidationError("Os dados do candidato estão desatualizados.")

            if not self.inscricao.candidato.pessoa.has_dados_suap_completos():
                raise ValidationError(
                    "Candidato não preencheu os dados necessários para a pré-matrícula."
                )

            from candidatos.models import Caracterizacao

            try:
                caracterizacao = Caracterizacao.objects.get(
                    candidato=self.inscricao.candidato.pessoa
                )
            except Caracterizacao.DoesNotExist:
                caracterizacao = None
            inicio_etapa = self.etapa.data_inicio
            dias_passados = dias_entre(inicio_etapa, date.today())
            has_caracterizacao_atualizada = (
                caracterizacao
                and caracterizacao.is_atualizado_recentemente(dias_passados)
            )
            if not caracterizacao:
                raise ValidationError(
                    "Os dados socioeconônicos do candidato não foram preenchidos."
                )
            elif not has_caracterizacao_atualizada:
                raise ValidationError(
                    "Os dados socioeconônicos do candidato estão desatualizados."
                )


class Matricula(models.Model):
    class Error(Exception):
        pass

    inscricao = models.ForeignKey(Inscricao, on_delete=models.CASCADE)
    etapa = models.ForeignKey(Etapa, on_delete=models.CASCADE)

    @property
    def modalidade(self):
        return self.inscricao.modalidade

    def __str__(self):
        return f"{self.inscricao.candidato}"

    class Meta:
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"


class ModalidadeEnum(IntEnum):
    ampla_concorrencia = 3
    renda_inferior = -2
    renda_inferior_cota_racial = -3
    cota_racial = -2
    rurais = -1
    deficientes = 2
    escola_publica = 10
    renda_inferior_cota_racial_pcd = 1
    renda_inferior_pcd = 9
    cota_racial_pcd = 10
    escola_publica_pcd = 11


@reversion.register()
class Vaga(models.Model):
    class TransicaoImpossivel(Exception):
        pass

    edicao = models.ForeignKey(Edicao, related_name="vagas", on_delete=models.CASCADE)
    curso = models.ForeignKey("cursos.CursoSelecao", on_delete=models.CASCADE)
    modalidade = models.ForeignKey(
        Modalidade, related_name="vagas", on_delete=models.CASCADE
    )
    modalidade_primaria = models.ForeignKey(
        Modalidade, related_name="vagas_originais", on_delete=models.CASCADE
    )
    candidato = models.ForeignKey(
        Candidato, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.edicao} {self.curso} {self.modalidade} - Livre={self.livre}"

    @classmethod
    def _criar(cls, edicao, curso, modalidade):
        return cls(
            edicao=edicao,
            curso=curso,
            modalidade=modalidade,
            modalidade_primaria=modalidade,
        )

    @classmethod
    def criar(cls, edicao, curso, modalidade):
        v = cls._criar(edicao, curso, modalidade)
        v.save()
        return v

    @classmethod
    def criar_varias(cls, quantidade, edicao, curso, modalidade):
        vagas = []
        for x in range(quantidade):
            v = cls._criar(edicao, curso, modalidade)
            vagas.append(v)

        cls.objects.bulk_create(vagas)

    @property
    def livre(self):
        return not bool(self.candidato)

    @property
    def ocupada(self):
        return not self.livre

    def _nova_transicao(self, modalidade_nova):

        if modalidade_nova == self.modalidade:
            return

        self.transicoes.add(
            RegistroTransicaoModalidadeVagas.objects.create(
                vaga=self, origem=self.modalidade, destino=modalidade_nova
            )
        )
        self.modalidade = modalidade_nova
        self.save()

    def set_proxima_modalidade(self):
        if not self.livre or self.modalidade.id == ModalidadeEnum.ampla_concorrencia:
            return
        try:
            transicao = TransicaoModalidade.get_destino(
                self.modalidade_primaria, self.modalidade
            )
            self._nova_transicao(transicao.destino)
            return self.modalidade
        except TransicaoModalidade.DoesNotExist:
            raise self.TransicaoImpossivel()

    def buscar_nova_modalidade(self):
        while self.quantidade_candidatos_inscritos < self.quantidade_vagas_no_curso:
            modalidade = self.modalidade
            self.set_proxima_modalidade()
            if self.modalidade == modalidade:
                break

    @property
    def quantidade_candidatos_inscritos(self):
        return Inscricao.objects.filter(
            modalidade=self.modalidade,
            curso=self.curso,
            edicao=self.edicao,
            chamada=None,
        ).count()

    @property
    def quantidade_vagas_no_curso(self):
        return Vaga.objects.filter(
            modalidade=self.modalidade,
            curso=self.curso,
            edicao=self.edicao,
            candidato__isnull=True,
        ).count()


class RegistroTransicaoModalidadeVagas(models.Model):
    vaga = models.ForeignKey(Vaga, related_name="transicoes", on_delete=models.CASCADE)
    origem = models.ForeignKey(
        Modalidade, related_name="origem_em_transacoes", on_delete=models.CASCADE
    )
    destino = models.ForeignKey(
        Modalidade, related_name="destino_em_transacoes", on_delete=models.CASCADE
    )
    criado_em = models.DateTimeField(auto_now_add=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.origem} --> {self.destino}"


class TransicaoModalidade(models.Model):
    modalidade_inicial = models.ForeignKey(Modalidade, on_delete=models.CASCADE)

    @staticmethod
    def get_destino(modalidade_inicial, origem):
        return TransicaoModalidadePossivel.objects.get(
            modalidade__modalidade_inicial=modalidade_inicial, origem=origem
        )

    class Meta:
        verbose_name = "Transição de modalidade"
        verbose_name_plural = "Transições de modalidade"

    def __str__(self):
        return str(self.modalidade_inicial)


class TransicaoModalidadePossivel(models.Model):
    modalidade = models.ForeignKey(TransicaoModalidade, on_delete=models.CASCADE)
    origem = models.ForeignKey(
        Modalidade, related_name="transicao_origem", on_delete=models.CASCADE
    )
    destino = models.ForeignKey(
        Modalidade, related_name="transicao_destino", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Transição de modalidade possível"
        verbose_name_plural = "Transições de modalidade possíveis"

    def __str__(self):
        return f"{self.origem} --> {self.destino}"


class AnaliseDocumental(models.Model):
    class AlreadyExists(Exception):
        pass

    confirmacao_interesse = models.OneToOneField(
        ConfirmacaoInteresse,
        verbose_name="Confirmação de interesse",
        help_text="Informe o nome do candidato. Somente aqueles que confirmaram interesse.",
        on_delete=models.CASCADE,
    )
    servidor_coordenacao = models.CharField(
        verbose_name="Servidor Responsável", max_length=255
    )
    observacao = models.TextField(verbose_name="Observações finais", max_length=255)
    data = models.DateField(verbose_name="Data da avaliação final")
    situacao_final = models.BooleanField(
        verbose_name="Situação final", choices=SITUACAO_CHOICES
    )

    class Meta:
        verbose_name = "Análise de Documentos"
        verbose_name_plural = "Análises de Documentos"
        ordering = ["confirmacao_interesse__inscricao__candidato"]

    def __str__(self):
        return str(self.confirmacao_interesse.inscricao)

    def is_deferida(self):
        return self.situacao_final

    def is_analise_cota(self):
        return (
            self.confirmacao_interesse.inscricao.modalidade_id
            != ModalidadeEnum.ampla_concorrencia
        )

    def inscricoes_convocacoes_concomitantes(self):
        inscricao = self.confirmacao_interesse.inscricao
        return inscricao.candidato.inscricoes.filter(
            chamada__etapa=inscricao.chamada.etapa
        ).exclude(pk=inscricao.pk)


class TipoAnalise(models.Model):
    TIPO_DOCUMENTACAO_BASICA = "DOCUMENTAÇÃO BÁSICA"
    TIPO_AVALIACAO_EEP = "AVALIAÇÃO EGRESSO DE ESCOLA PÚBLICA"
    TIPO_AVALIACAO_SOCIOECONOMICA = "AVALIAÇÃO SOCIOECONÔMICA"
    TIPO_AVALIACAO_MEDICA = "AVALIAÇÃO MÉDICA"

    nome = models.CharField(
        verbose_name="Tipo de avaliação", max_length=255, unique=True
    )
    setor_responsavel = models.CharField(
        verbose_name="Setor responsável", max_length=255
    )
    descricao = models.TextField(verbose_name="Descrição", max_length=1500)
    modalidade = models.ManyToManyField(Modalidade, related_name="tipos_analise")

    class Meta:
        verbose_name = "Tipo de análise de documento"
        verbose_name_plural = "Tipos de análise de documento"
        ordering = ["pk"]

    def __str__(self):
        return self.nome


class AvaliacaoDocumental(models.Model):
    tipo_analise = models.ForeignKey(
        TipoAnalise,
        related_name="tipo_analise",
        verbose_name="Tipo de análise",
        on_delete=models.CASCADE,
    )
    servidor_setor = models.CharField(verbose_name="Avaliador", max_length=255)
    analise_documental = models.ForeignKey(
        AnaliseDocumental, related_name="analise_documental", on_delete=models.CASCADE
    )
    data = models.DateField(verbose_name="Data da avaliação final")
    observacao = models.TextField(
        verbose_name="Observação",
        max_length=255,
        blank=True,
        help_text="Informe aqui caso o avaliador tenha registrado alguma observação sobre sobre a avaliação.",
    )
    situacao = models.BooleanField(verbose_name="Situação", choices=SITUACAO_CHOICES)

    class Meta:
        unique_together = ("tipo_analise", "analise_documental")
        verbose_name = "Avaliação Documental"
        verbose_name_plural = "Avaliações Documentais"

    @cached_property
    def etapa(self):
        return self.analise_documental.confirmacao_interesse.etapa

    def pode_editar(self):
        return (
            self.etapa
            and not self.etapa.encerrada
            and self.etapa.get_cronograma_convocacao("ANALISE").is_vigente()
        )

    def pode_excluir(self):
        return self.pode_editar()

    def clean(self):
        super().clean()
        if self.analise_documental_id and not self.pode_editar():
            raise ValidationError(
                "Não é possível modificar esta avaliação, entre em contato com o controle acadêmico"
                " do campus para mais detalhes."
            )


class Recurso(models.Model):
    class Error(Exception):
        pass

    analise_documental = models.OneToOneField(
        AnaliseDocumental,
        verbose_name="Análise documental",
        help_text="Informe o nome do candidato. Somente aqueles que possuem análise documental.",
        on_delete=models.CASCADE,
    )
    protocolo = models.CharField(verbose_name="Protocolo", max_length=255)
    justificativa = models.TextField(verbose_name="Justificativa", max_length=500)
    status_recurso = models.CharField(
        max_length=10, verbose_name="Status do recurso", choices=StatusRecurso.choices()
    )

    def __str__(self):
        return f"{self.analise_documental}"

    class Meta:
        verbose_name = "Recurso"
        verbose_name_plural = "Recursos"
        ordering = ["analise_documental__confirmacao_interesse__inscricao__candidato"]


class Resultado(models.Model):
    inscricao = models.ForeignKey(Inscricao, on_delete=models.CASCADE)
    etapa = models.ForeignKey(Etapa, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10, verbose_name="Situação", choices=Status.choices()
    )
    observacao = models.CharField(verbose_name="Observação", max_length=525)

    def __str__(self):
        return f"{self.inscricao.candidato}"

    class Meta:
        verbose_name = "Resultado"
        verbose_name_plural = "Resultados"
