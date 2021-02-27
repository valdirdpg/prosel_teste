from django.db import models
from django.utils.formats import localize

from cursos.models import CursoSelecao
from processoseletivo.models import ModalidadeEnum
from psct.models import analise as analise_models
from psct.models.inscricao import Modalidade, ModalidadeVagaCursoEdital
from psct.models.recurso import ModelDate


class ResultadoPreliminar(ModelDate):
    fase = models.ForeignKey(
        analise_models.FaseAnalise,
        verbose_name="Fase de Análise",
        on_delete=models.PROTECT,
        related_name="resultados_preliminares",
    )

    class Meta:
        verbose_name = "Resultado Preliminar"
        verbose_name_plural = "Resultados preliminares"

    def __str__(self):
        date = localize(self.data_cadastro)
        return f"Resultado Preliminar da {self.fase} de {date}"

    def get_inscricoes(self, curso, modalidade):
        try:
            is_ampla = modalidade.equivalente_id == ModalidadeEnum.ampla_concorrencia
            vagas = VagasResultadoPreliminar.objects.get(
                resultado_curso__resultado=self,
                resultado_curso__curso=curso,
                modalidade=modalidade,
            )

            filters = {}
            if not is_ampla:
                filters["inscricao__modalidade_cota"] = modalidade

            return ResultadoPreliminarInscricao.objects.filter(
                resultado_curso__resultado=self, resultado_curso__curso=curso, **filters
            )[: vagas.quantidade]
        except VagasResultadoPreliminar.DoesNotExist:
            return ResultadoPreliminarInscricao.objects.none()

    def get_vagas(self, curso, modalidade):
        return VagasResultadoPreliminar.objects.get(
            resultado_curso__resultado=self,
            resultado_curso__curso=curso,
            modalidade=modalidade,
        )

    def get_resultado_inscricao(self, inscricao):
        return ResultadoPreliminarInscricao.objects.get(
            inscricao=inscricao, resultado_curso__resultado=self
        )

    def get_classificacao(self, inscricao) -> tuple:
        resultado_inscricao = self.get_resultado_inscricao(inscricao)
        return resultado_inscricao.classificacao, resultado_inscricao.classificacao_cota

    def is_classificado_modalidade(self, inscricao, modalidade) -> bool:
        vagas = self.get_vagas(inscricao.curso, modalidade)
        return inscricao in [i.inscricao for i in vagas.get_classificados()]

    @staticmethod
    def get_ampla():
        return Modalidade.objects.get(equivalente_id=ModalidadeEnum.ampla_concorrencia)

    def is_classificado(self, inscricao) -> bool:
        is_ampla = inscricao.modalidade_cota.equivalente_id == ModalidadeEnum.ampla_concorrencia
        classificado = self.is_classificado_modalidade(
            inscricao, inscricao.modalidade_cota
        )
        if is_ampla:
            return classificado
        return classificado or self.is_classificado_modalidade(
            inscricao, self.get_ampla()
        )

    def em_lista_espera_modalidade(self, inscricao, modalidade) -> bool:
        vagas = self.get_vagas(inscricao.curso, modalidade)

        classificacao_geral, classificacao_cota = self.get_classificacao(inscricao)
        classificado = self.is_classificado(inscricao)

        if modalidade.is_ampla:
            classificacao = classificacao_geral
        else:
            classificacao = classificacao_cota

        return (not classificado) and classificacao <= vagas.get_limite_lista_espera()

    def em_lista_espera(self, inscricao) -> bool:
        lista_espera = self.em_lista_espera_modalidade(
            inscricao, inscricao.modalidade_cota
        )
        if inscricao.is_ampla_concorrencia:
            return lista_espera
        return lista_espera or self.em_lista_espera_modalidade(
            inscricao, self.get_ampla()
        )

    def get_indeferimento(self, inscricao) -> str:
        qs = ResultadoPreliminarInscricaoIndeferida.objects.filter(
            resultado=self, inscricao=inscricao
        )
        if qs.exists():
            resultado_inscricao = qs.first()
            return resultado_inscricao.justiticativa_indeferimento


class ResultadoPreliminarHomologado(ModelDate):
    edital = models.OneToOneField(
        analise_models.Edital,
        verbose_name="Edital",
        on_delete=models.PROTECT,
        related_name="resultado_preliminar",
    )
    resultado = models.ForeignKey(
        ResultadoPreliminar, verbose_name="Resultado", on_delete=models.PROTECT
    )

    class Meta:
        verbose_name = "Resultado Preliminar Homologado"
        verbose_name_plural = "Resultados preliminares homologados"

    def __str__(self):
        return f"Resultado Preliminar do {self.edital}"

    def is_final(self):
        return False


class ResultadoFinal(ModelDate):
    edital = models.OneToOneField(
        analise_models.Edital,
        verbose_name="Edital",
        on_delete=models.PROTECT,
        related_name="resultado",
    )
    resultado = models.ForeignKey(
        ResultadoPreliminar, verbose_name="Resultado", on_delete=models.PROTECT
    )

    class Meta:
        verbose_name = "Resultado Final"
        verbose_name_plural = "Resultados Final"

    def is_final(self):
        return True


class ResultadoPreliminarCurso(ModelDate):
    resultado = models.ForeignKey(
        ResultadoPreliminar,
        verbose_name="Resultado Preliminar",
        related_name="cursos",
        on_delete=models.PROTECT,
    )
    curso = models.ForeignKey(
        CursoSelecao, verbose_name="Curso", on_delete=models.PROTECT
    )

    class Meta:
        verbose_name_plural = "Resultados preliminar de cursos"
        verbose_name = "Resultado preliminnar de curso"
        ordering = ("curso__curso__nome",)


class ResultadoPreliminarInscricao(ModelDate):
    resultado_curso = models.ForeignKey(
        ResultadoPreliminarCurso,
        verbose_name="Resultado Preliminar Curso",
        related_name="inscricoes",
        on_delete=models.PROTECT,
    )
    classificacao = models.IntegerField(verbose_name="Classificação Geral")
    classificacao_cota = models.IntegerField(
        verbose_name="Classificação na cota", null=True, blank=True
    )
    inscricao_preanalise = models.ForeignKey(
        analise_models.InscricaoPreAnalise,
        verbose_name="Inscrição Pré-análise",
        on_delete=models.PROTECT,
        related_name="resultados_preliminares",
    )
    inscricao = models.ForeignKey(
        analise_models.Inscricao,
        verbose_name="Inscrição",
        on_delete=models.PROTECT,
        related_name="resultados_preliminares",
    )
    justiticativa_indeferimento = models.ForeignKey(
        analise_models.JustificativaIndeferimento,
        verbose_name="Justificativa do Indeferimento",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name_plural = "Resultados preliminares inscrição"
        verbose_name = "Resultado preliminar inscrição"
        ordering = ("classificacao",)


class ResultadoPreliminarInscricaoIndeferida(ModelDate):
    resultado = models.ForeignKey(
        ResultadoPreliminar,
        verbose_name="Resultado Preliminar",
        related_name="inscricoes_indeferidas",
        on_delete=models.PROTECT,
    )
    inscricao_preanalise = models.ForeignKey(
        analise_models.InscricaoPreAnalise,
        verbose_name="Inscrição Pré-análise",
        on_delete=models.PROTECT,
    )
    inscricao = models.ForeignKey(
        analise_models.Inscricao, verbose_name="Inscrição", on_delete=models.PROTECT
    )
    justiticativa_indeferimento = models.ForeignKey(
        analise_models.JustificativaIndeferimento,
        verbose_name="Justificativa do Indeferimento",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name_plural = "Resultados prel. inscrição indeferida"
        verbose_name = "Resultado prel. inscrição indeferida"


class VagasResultadoPreliminar(ModelDate):
    resultado_curso = models.ForeignKey(
        ResultadoPreliminarCurso,
        on_delete=models.PROTECT,
        verbose_name="Resultado Preliminar Curso",
        related_name="vagas",
    )
    modalidade = models.ForeignKey(
        Modalidade, verbose_name="Modalidade", on_delete=models.PROTECT
    )
    quantidade = models.IntegerField(verbose_name="Quantidade", default=0)

    class Meta:
        verbose_name = "Vagas do resultado preliminar"
        verbose_name_plural = "Vagas dos resultados preliminares"

    def get_vagas_edital(self):
        return ModalidadeVagaCursoEdital.objects.get(
            modalidade=self.modalidade,
            curso_edital__curso=self.resultado_curso.curso,
            curso_edital__edital=self.resultado_curso.resultado.fase.edital,
        )

    def get_vagas_resultado(self) -> int:
        return self.get_classificados().count()

    def get_limite_lista_espera(self) -> int:
        vagas_edital = self.get_vagas_edital()
        multiplicador = (
            vagas_edital.curso_edital.edital.processo_inscricao.multiplicador
        )
        return vagas_edital.quantidade_vagas * multiplicador

    def get_classificados(self):
        from psct.export import get_inscricoes

        return get_inscricoes(
            self.resultado_curso.resultado, self.resultado_curso.curso, self.modalidade
        )
