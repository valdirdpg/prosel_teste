import datetime

from django.utils import timezone
from freezegun import freeze_time

import base.tests.recipes
from base.tests.mixins import UserTestMixin
from cursos.permissions import DiretoresdeEnsino
from cursos.recipes import curso_selecao_subsequente
from editais.tests.recipes import edital_abertura
from processoseletivo.models import ModalidadeEnum
from processoseletivo.recipes import edicao
from psct.tests import recipes
from .. import models
from .. import permissions


class EditalTestData:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.edital = edital_abertura.make()


class CursoTestData:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        DiretoresdeEnsino().sync()
        cls.curso = recipes.curso_psct.make()


class ProcessoSeletivoTestData:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.edicao = edicao.make()
        cls.processo_seletivo = cls.edicao.processo_seletivo


class ModalidadeAmplaConcorrenciaSetUpTestData:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.modalidade_ampla = models.Modalidade.objects.get(
            equivalente=ModalidadeEnum.ampla_concorrencia
        )


class CandidatoMixin(UserTestMixin):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user_candidato = cls.usuario_base
        cls.candidato = recipes.candidato.make(
            nome=cls.user_candidato.get_full_name(),
            email=cls.user_candidato.email,
            user=cls.user_candidato,
        )
        permissions.CandidatosPSCT.add_user(user=cls.user_candidato)


class ProcessoInscricaoMixin(
    EditalTestData, ProcessoSeletivoTestData, ModalidadeAmplaConcorrenciaSetUpTestData
):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Preparação dos dados do processo seletivo para realizar os testes de inscrição
        DiretoresdeEnsino().sync()
        cls.curso_tecnico = curso_selecao_subsequente.make()
        cls.psct_subsequente = recipes.processo_inscricao.make(
            edital=cls.edital,
            cursos=[cls.curso_tecnico],
            formacao=models.ProcessoInscricao.SUBSEQUENTE
        )
        recipes.modalidade_vaga_curso_edital.make(
            curso_edital__edital=cls.edital,
            curso_edital__curso=cls.curso_tecnico,
            modalidade=cls.modalidade_ampla
        )
        cls.modeloquestionario = recipes.modelo_questionario.make(edital=cls.edital)


class FaseAnaliseTestData:
    @classmethod
    def setUpTestData(cls):
        permissions.AvaliadorPSCT().sync()
        permissions.HomologadorPSCT().sync()

        cls.yesterday = timezone.now() - datetime.timedelta(days=1)
        with freeze_time(cls.yesterday):
            super().setUpTestData()

        cls.grupo_avaliadores = recipes.grupo_edital.make(edital=cls.edital)
        cls.grupo_avaliadores.grupo.user_set.add(base.tests.recipes.user.make())
        cls.grupo_homologadores = recipes.grupo_edital.make(edital=cls.edital)
        cls.grupo_homologadores.grupo.user_set.add(base.tests.recipes.user.make())

        cls.faseanalise_recipe = recipes.fase_analise.extend(
            edital=cls.edital,
            avaliadores=cls.grupo_avaliadores,
        )
        cls.fase_analise = cls.faseanalise_recipe.make(
            requer_homologador=True,
            homologadores=cls.grupo_homologadores,
        )


class AvaliadorPSCTTestData:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.usuario_avaliador = base.tests.recipes.user.make()
        permissions.AvaliadorPSCT().sync()
        permissions.AvaliadorPSCT.add_user(cls.usuario_avaliador)


class HomologadorPSCTTestData:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.usuario_homologador = base.tests.recipes.user.make()
        permissions.HomologadorPSCT().sync()
        permissions.HomologadorPSCT.add_user(cls.usuario_homologador)


class AdministradorPSCTTestData:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.usuario_administrador = base.tests.recipes.user.make()
        permissions.AdministradoresPSCT().sync()
        permissions.AdministradoresPSCT.add_user(cls.usuario_administrador)


class InscricaoPreAnaliseTestData:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.AvaliadorPSCT().sync()
        cls.processo_inscricao = recipes.processo_inscricao.make(edital=cls.edital)
        cls.inscricao_original = recipes.inscricao.make(
            edital=cls.edital,
            curso=cls.curso,
        )
        cls.inscricao = recipes.inscricao_pre_analise.make(
            candidato=cls.inscricao_original.candidato,
            fase__edital=cls.edital,
            curso=cls.curso,
            modalidade=cls.inscricao_original.modalidade_cota,
        )
