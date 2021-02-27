import datetime
from unittest import mock

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

import base.tests.recipes
from cursos import choices
from .. import mixins
from .. import recipes
from ... import permissions
from ...models import analise as models


class FaseAnaliseModelTestCase(
    mixins.FaseAnaliseTestData,
    mixins.ProcessoInscricaoMixin,
    TestCase
):
    def test_str_deve_conter_nome_da_fase_numero_e_ano_do_edital(self):
        self.assertEqual(
            f"{self.fase_analise.nome} - Edital {self.edital.numero}/{self.edital.ano}",
            str(self.fase_analise),
        )

    def test_clean_data_encerramento_anterior_ao_inicio(self):
        fase = self.faseanalise_recipe.make(data_encerramento=self.yesterday)
        with self.assertRaises(ValidationError) as ex:
            fase.clean()
        self.assertIn(
            "A data de encerramento não pode ser inferior ao seu início",
            ex.exception.message_dict.get("data_encerramento"),
        )

    def test_clean_data_encerramento_inferior_ao_resultado(self):
        fase = self.faseanalise_recipe.make(data_resultado=self.yesterday)
        with self.assertRaises(ValidationError) as ex:
            fase.clean()
        self.assertIn(
            (
                "A data de divulgação do resultado não pode ser inferior ao encerramento "
                "do período de análise"
            ),
            ex.exception.message_dict.get("data_resultado"),
        )

    def test_clean_fase_analise_iniciando_antes_do_fim_das_inscricoes(self):
        fase = self.faseanalise_recipe.make(data_inicio=self.yesterday)
        with self.assertRaises(ValidationError) as ex:
            fase.clean()
        self.assertIn(
            "A fase de análise só pode começar após o encerramento das inscrições",
            ex.exception.message_dict.get("data_inicio"),
        )

    def test_clean_grupo_avaliadores_de_edital_diferente(self):
        fase = self.faseanalise_recipe.make(avaliadores=recipes.grupo_edital.make)
        with self.assertRaises(ValidationError) as ex:
            fase.clean()
        self.assertIn(
            "O grupo de avaliadores não pertence ao edital selecionado",
            ex.exception.message_dict.get("avaliadores"),
        )

    def test_clean_grupo_homologadores_de_edital_diferente(self):
        fase = self.faseanalise_recipe.make(homologadores=recipes.grupo_edital.make)
        with self.assertRaises(ValidationError) as ex:
            fase.clean()
        self.assertIn(
            "O grupo de homologadores não pertence ao edital selecionado",
            ex.exception.message_dict.get("homologadores"),
        )

    def test_clean_sem_grupo_homologadores(self):
        fase = self.faseanalise_recipe.make(requer_homologador=True)
        with self.assertRaises(ValidationError) as ex:
            fase.clean()
        self.assertIn(
            "O grupo de homologadores não foi definido",
            ex.exception.message_dict.get("homologadores"),
        )

    def test_clean_grupo_homologadores_sem_usuarios(self):
        grupo_homologadores_vazio = recipes.grupo_edital.make(edital=self.edital)
        fase = self.faseanalise_recipe.make(homologadores=grupo_homologadores_vazio)
        with self.assertRaises(ValidationError) as ex:
            fase.clean()
        self.assertIn(
            "O grupo de homologadores está vazio.",
            ex.exception.message_dict.get("homologadores"),
        )

    def test_fase_analise_deve_estar_acontecendo(self):
        fase = self.faseanalise_recipe.make(
            data_encerramento=timezone.now() + datetime.timedelta(days=1),
            data_resultado=timezone.now() + datetime.timedelta(days=2)
        )
        self.assertTrue(fase.acontecendo)

    def test_fase_analise_nao_deve_estar_acontecendo(self):
        self.assertFalse(self.fase_analise.acontecendo)

    def test_avaliador_deve_receber_permissao_psct(self):
        grupo_avaliador_psct = Group.objects.get(name="Avaliador PSCT")
        usuario = base.tests.recipes.user.make()
        self.assertNotIn(usuario, grupo_avaliador_psct.user_set.all())

        self.grupo_avaliadores.grupo.user_set.add(usuario)
        self.fase_analise.save()
        self.assertIn(usuario, grupo_avaliador_psct.user_set.all())

    def test_homologador_deve_receber_permissao_psct(self):
        grupo_homologador_psct = Group.objects.get(name="Homologador PSCT")
        usuario = base.tests.recipes.user.make()
        self.assertNotIn(usuario, grupo_homologador_psct.user_set.all())

        self.grupo_homologadores.grupo.user_set.add(usuario)
        self.fase_analise.save()
        self.assertIn(usuario, grupo_homologador_psct.user_set.all())

    def test_usuario_eh_avaliador_da_fase(self):
        usuario = base.tests.recipes.user.make()
        self.grupo_avaliadores.grupo.user_set.add(usuario)
        self.assertTrue(self.fase_analise.eh_avaliador(usuario))

    def test_usuario_eh_homologador_da_fase(self):
        usuario = base.tests.recipes.user.make()
        self.grupo_homologadores.grupo.user_set.add(usuario)
        self.assertTrue(self.fase_analise.eh_homologador(usuario))


class SituacaoInscricaoPreAnaliseTestCase(
    mixins.FaseAnaliseTestData,
    mixins.ProcessoInscricaoMixin,
    TestCase
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.avaliador_a = cls.grupo_avaliadores.grupo.user_set.first()
        cls.avaliador_b = base.tests.recipes.user.make()
        cls.grupo_avaliadores.grupo.user_set.add(cls.avaliador_b)

        cls.fase_analise.quantidade_avaliadores = 2
        cls.fase_analise.save()

    def setUp(self):
        super().setUp()
        self.inscricao = recipes.inscricao_pre_analise.make(
            fase=self.fase_analise,
            curso=self.curso_tecnico,
            modalidade=self.modalidade_ampla,
            situacao=models.SituacaoInscricao.SEM_AVALIADORES.name,
        )

    def test_inscricao_recem_criada_deve_ter_situacao_sem_avaliador(self):
        self.assertEquals(models.SituacaoInscricao.SEM_AVALIADORES.name, self.inscricao.situacao)

    def test_situacao_inscricao_deve_ser_aguardando_homologador_em_avaliacoes_conflitantes(self):
        recipes.avaliacao_avaliador.make(
            inscricao=self.inscricao,
            avaliador=self.avaliador_a
        )
        recipes.avaliacao_avaliador_indeferida.make(
            inscricao=self.inscricao,
            avaliador=self.avaliador_b,
        )
        self.assertEquals(
            models.SituacaoInscricao.AGUARDANDO_HOMOLOGADOR.name,
            self.inscricao.situacao
        )

    def test_situacao_inscricao_deve_ser_aguardando_homologador_em_indeferimentos_divergentes(self):
        recipes.avaliacao_avaliador_indeferida.make(
            inscricao=self.inscricao,
            avaliador=self.avaliador_a,
        )
        recipes.avaliacao_avaliador_indeferida.make(
            inscricao=self.inscricao,
            avaliador=self.avaliador_b,
        )
        self.assertEquals(
            models.SituacaoInscricao.AGUARDANDO_HOMOLOGADOR.name,
            self.inscricao.situacao
        )

    def test_situacao_inscricao_deve_ser_deferida(self):
        recipes.avaliacao_avaliador.make(
            inscricao=self.inscricao,
            avaliador=self.avaliador_a
        )
        recipes.avaliacao_avaliador.make(
            inscricao=self.inscricao,
            avaliador=self.avaliador_b,
        )
        self.assertEquals(models.SituacaoInscricao.DEFERIDA.name, self.inscricao.situacao)

    def test_situacao_inscricao_deve_ser_indeferida(self):
        indeferimento = recipes.justificativa_indeferimento.make()
        recipes.avaliacao_avaliador_indeferida.make(
            inscricao=self.inscricao,
            avaliador=self.avaliador_a,
            texto_indeferimento=indeferimento
        )
        recipes.avaliacao_avaliador_indeferida.make(
            inscricao=self.inscricao,
            avaliador=self.avaliador_b,
            texto_indeferimento=indeferimento
        )
        self.assertEquals(models.SituacaoInscricao.INDEFERIDA.name, self.inscricao.situacao)


class InscricaoPreAnaliseTestCase(mixins.EditalTestData, mixins.CursoTestData, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.AvaliadorPSCT().sync()
        permissions.HomologadorPSCT().sync()
        cls.processo_inscricao = recipes.processo_inscricao.make(edital=cls.edital)
        cls.fase_analise = recipes.fase_analise.make(edital=cls.edital)
        cls.inscricaopreanalise = recipes.inscricao_pre_analise.make(
            fase=cls.fase_analise,
            curso=cls.curso,
        )

    def test_str_deve_conter_candidato_e_curso(self):
        self.assertEqual(
            f"{self.inscricaopreanalise.candidato} - {self.curso}",
            str(self.inscricaopreanalise)
        )

    def test_property_inscricao_deve_retornar_inscricao_original(self):
        inscricao_original = recipes.inscricao.make(
            candidato=self.inscricaopreanalise.candidato,
            edital=self.inscricaopreanalise.fase.edital,
            curso=self.inscricaopreanalise.curso,
            modalidade_cota=self.inscricaopreanalise.modalidade,
        )
        self.assertEqual(inscricao_original, self.inscricaopreanalise.inscricao)

    def test_property_avaliacao_deve_retornar_avaliacao_do_homologador(self):
        avaiacao_homologador = recipes.avaliacao_homologador.make(
            inscricao=self.inscricaopreanalise
        )
        self.assertEqual(avaiacao_homologador, self.inscricaopreanalise.avaliacao)

    def test_get_avaliadores_deve_retornar_os_avaliadores_que_possuem_a_inscricao_na_mailbox(self):
        mailbox_avaliador_a = recipes.mailbox_avaliador_inscricao.make(fase=self.fase_analise)
        mailbox_avaliador_b = recipes.mailbox_avaliador_inscricao.make(fase=self.fase_analise)
        mailbox_avaliador_a.inscricoes.add(self.inscricaopreanalise)
        mailbox_avaliador_b.inscricoes.add(self.inscricaopreanalise)
        self.assertIn(mailbox_avaliador_a.avaliador, self.inscricaopreanalise.get_avaliadores())
        self.assertIn(mailbox_avaliador_b.avaliador, self.inscricaopreanalise.get_avaliadores())

    def test_get_homologador_deve_retornar_o_homologador_que_possui_a_inscricao_na_mailbox(self):
        mailbox_homologador = recipes.mailbox_homologador_inscricao.make(fase=self.fase_analise)
        mailbox_homologador.inscricoes.add(self.inscricaopreanalise)
        self.assertEqual(
            mailbox_homologador.homologador,
            self.inscricaopreanalise.get_homologador()
        )

    def test_create_from_raw_inscricao_deve_criar_inscricaopreanalise_para_a_fase(self):
        total_inscricoes = models.InscricaoPreAnalise.objects.count()
        self.edital.processo_inscricao.formacao = self.edital.processo_inscricao.SUBSEQUENTE
        self.edital.processo_inscricao.save()
        self.curso.formacao = choices.Formacao.SUBSEQUENTE.name
        self.curso.save()
        inscricao = recipes.inscricao.make(
            edital=self.edital,
            curso=self.curso,
        )
        models.InscricaoPreAnalise.create_from_raw_inscricao(
            inscricao=inscricao, fase=self.fase_analise
        )
        self.assertEqual(total_inscricoes + 1, models.InscricaoPreAnalise.objects.count())

    def test_create_many_deve_criar_insricaopreanalise_para_todas_inscricoes_validas(self):
        total_inscricoes = models.InscricaoPreAnalise.objects.count()
        self.edital.processo_inscricao.formacao = choices.Formacao.SUBSEQUENTE.name
        self.edital.processo_inscricao.save()
        inscricao = recipes.inscricao.make(
            edital=self.edital,
            curso=self.curso,
            aceite=True,
        )
        recipes.comprovante.make(inscricao=inscricao)
        models.InscricaoPreAnalise.create_many(fase=self.fase_analise)
        self.assertEqual(total_inscricoes + 1, models.InscricaoPreAnalise.objects.count())

    @mock.patch("psct.models.FaseAnalise.eh_homologador")
    @mock.patch("psct.models.FaseAnalise.eh_avaliador")
    @mock.patch("psct.models.InscricaoPreAnalise.empilhada", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.InscricaoPreAnalise.indeferida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.FaseAnalise.get_fase_ajuste")
    def test_property_pode_empilhar_deve_retornar_false_quando_nao_existir_fase_de_ajuste_de_notas(
            self, get_fase_ajuste, indeferida, empilhada, eh_avaliador, eh_homologador
    ):
        get_fase_ajuste.return_value = None
        indeferida.return_value = True
        empilhada.return_value = False
        eh_avaliador.return_value = True
        eh_homologador.return_value = False
        is_administrador = False
        self.assertFalse(
            self.inscricaopreanalise.pode_empilhar(
                user=mock.Mock(), is_administrador=is_administrador
            )
        )

    @mock.patch("psct.models.FaseAnalise.eh_homologador")
    @mock.patch("psct.models.FaseAnalise.eh_avaliador")
    @mock.patch("psct.models.InscricaoPreAnalise.empilhada", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.InscricaoPreAnalise.indeferida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.FaseAnalise.get_fase_ajuste")
    def test_property_pode_empilhar_deve_retornar_false_quando_inscricao_nao_for_indeferida(
            self, get_fase_ajuste, indeferida, empilhada, eh_avaliador, eh_homologador
    ):
        get_fase_ajuste.return_value = mock.Mock()
        indeferida.return_value = False
        empilhada.return_value = False
        eh_avaliador.return_value = True
        eh_homologador.return_value = False
        is_administrador = False
        self.assertFalse(
            self.inscricaopreanalise.pode_empilhar(
                user=mock.Mock(), is_administrador=is_administrador
            )
        )

    @mock.patch("psct.models.FaseAnalise.eh_homologador")
    @mock.patch("psct.models.FaseAnalise.eh_avaliador")
    @mock.patch("psct.models.InscricaoPreAnalise.empilhada", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.InscricaoPreAnalise.indeferida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.FaseAnalise.get_fase_ajuste")
    def test_property_pode_empilhar_deve_retornar_false_quando_inscricao_ja_for_empilhada(
            self, get_fase_ajuste, indeferida, empilhada, eh_avaliador, eh_homologador
    ):
        get_fase_ajuste.return_value = mock.Mock()
        indeferida.return_value = True
        empilhada.return_value = True
        eh_avaliador.return_value = True
        eh_homologador.return_value = False
        is_administrador = False
        self.assertFalse(
            self.inscricaopreanalise.pode_empilhar(
                user=mock.Mock(), is_administrador=is_administrador
            )
        )

    @mock.patch("psct.models.FaseAnalise.eh_homologador")
    @mock.patch("psct.models.FaseAnalise.eh_avaliador")
    @mock.patch("psct.models.InscricaoPreAnalise.empilhada", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.InscricaoPreAnalise.indeferida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.FaseAnalise.get_fase_ajuste")
    def test_property_pode_empilhar_deve_retornar_false_quando_usuario_nao_for_avaliador_homologador_ou_administrador(
            self, get_fase_ajuste, indeferida, empilhada, eh_avaliador, eh_homologador
    ):
        get_fase_ajuste.return_value = mock.Mock()
        indeferida.return_value = True
        empilhada.return_value = False
        eh_avaliador.return_value = False
        eh_homologador.return_value = False
        is_administrador = False
        self.assertFalse(
            self.inscricaopreanalise.pode_empilhar(
                user=mock.Mock(), is_administrador=is_administrador
            )
        )

    @mock.patch("psct.models.FaseAnalise.eh_homologador")
    @mock.patch("psct.models.FaseAnalise.eh_avaliador")
    @mock.patch("psct.models.InscricaoPreAnalise.empilhada", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.InscricaoPreAnalise.indeferida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.FaseAnalise.get_fase_ajuste")
    def test_property_pode_empilhar_deve_retornar_true_quando_usuario_for_avaliador(
            self, get_fase_ajuste, indeferida, empilhada, eh_avaliador, eh_homologador
    ):
        get_fase_ajuste.return_value = mock.Mock()
        indeferida.return_value = True
        empilhada.return_value = False
        eh_avaliador.return_value = True
        eh_homologador.return_value = False
        is_administrador = False
        self.assertTrue(
            self.inscricaopreanalise.pode_empilhar(
                user=mock.Mock(), is_administrador=is_administrador
            )
        )

    @mock.patch("psct.models.FaseAnalise.eh_homologador")
    @mock.patch("psct.models.FaseAnalise.eh_avaliador")
    @mock.patch("psct.models.InscricaoPreAnalise.empilhada", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.InscricaoPreAnalise.indeferida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.FaseAnalise.get_fase_ajuste")
    def test_property_pode_empilhar_deve_retornar_true_quando_usuario_for_homologador(
            self, get_fase_ajuste, indeferida, empilhada, eh_avaliador, eh_homologador
    ):
        get_fase_ajuste.return_value = mock.Mock()
        indeferida.return_value = True
        empilhada.return_value = False
        eh_avaliador.return_value = False
        eh_homologador.return_value = True
        is_administrador = False
        self.assertTrue(
            self.inscricaopreanalise.pode_empilhar(
                user=mock.Mock(), is_administrador=is_administrador
            )
        )

    @mock.patch("psct.models.FaseAnalise.eh_homologador")
    @mock.patch("psct.models.FaseAnalise.eh_avaliador")
    @mock.patch("psct.models.InscricaoPreAnalise.empilhada", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.InscricaoPreAnalise.indeferida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.FaseAnalise.get_fase_ajuste")
    def test_property_pode_empilhar_deve_retornar_true_quando_usuario_for_administrador(
            self, get_fase_ajuste, indeferida, empilhada, eh_avaliador, eh_homologador
    ):
        get_fase_ajuste.return_value = mock.Mock()
        indeferida.return_value = True
        empilhada.return_value = False
        eh_avaliador.return_value = False
        eh_homologador.return_value = False
        is_administrador = True
        self.assertTrue(
            self.inscricaopreanalise.pode_empilhar(
                user=mock.Mock(), is_administrador=is_administrador
            )
        )

    def test_property_empilhada_deve_retornar_false_quando_inscricao_nao_estiver_em_pilhainscricaoajuste(
            self
    ):
        fase_ajuste = recipes.fase_ajuste_pontuacao.make(fase_analise=self.fase_analise)
        recipes.pilha_inscricao_ajuste.make(fase=fase_ajuste)
        self.assertFalse(self.inscricaopreanalise.empilhada)

    def test_property_empilhada_deve_retornar_true_quando_inscricao_estiver_em_pilhainscricaoajuste(
            self
    ):
        fase_ajuste = recipes.fase_ajuste_pontuacao.make(fase_analise=self.fase_analise)
        pilha = recipes.pilha_inscricao_ajuste.make(fase=fase_ajuste)
        pilha.inscricoes.add(self.inscricaopreanalise)
        self.assertTrue(self.inscricaopreanalise.empilhada)

    def test_property_motivo_indeferimeno_deve_retornar_indeferimento_especial(self):
        inscricao_pre_analise = recipes.inscricao_pre_analise.make(
            fase=self.fase_analise,
            curso=self.curso,
            situacao=models.SituacaoInscricao.INDEFERIDA.name
        )
        indeferimento_especial = recipes.indeferimento_especial.make(
            inscricao=inscricao_pre_analise
        )
        self.assertEqual(
            indeferimento_especial.motivo_indeferimento,
            inscricao_pre_analise.motivo_indeferimento
        )


class MailBoxAvaliadorInscricaoTestCase(mixins.CursoTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.AvaliadorPSCT().sync()
        cls.mailbox_avaliador = recipes.mailbox_avaliador_inscricao.make()
        cls.inscricaopreanalise = recipes.inscricao_pre_analise.make(
            fase=cls.mailbox_avaliador.fase,
            curso=cls.curso,
        )

    def test_str_deve_conter_avaliador(self):
        self.assertEqual(
            f"Caixa de Inscrições do Avaliador {self.mailbox_avaliador.avaliador}",
            str(self.mailbox_avaliador)
        )

    def test_method_add_deve_adicionar_inscricao_a_mailbox(self):
        total_inscricoes = self.mailbox_avaliador.inscricoes.count()
        self.mailbox_avaliador.add(self.inscricaopreanalise)
        self.assertEqual(total_inscricoes + 1, self.mailbox_avaliador.inscricoes.count())

    def test_method_add_deve_atualizar_progresso_de_analise_de_inscricoes(self):
        progresso_analise = recipes.progresso_analise.make(
            modalidade=self.inscricaopreanalise.modalidade,
            fase=self.inscricaopreanalise.fase,
            curso=self.inscricaopreanalise.curso
        )
        total_em_analise = progresso_analise.em_analise
        self.mailbox_avaliador.add(self.inscricaopreanalise)
        progresso_analise_atualizado = models.ProgressoAnalise.objects.get(pk=progresso_analise.id)
        self.assertEqual(total_em_analise + 1, progresso_analise_atualizado.em_analise)

    def test_property_possui_inscricao_pendente_deve_retornar_false_se_mailbox_estiver_vazia(self):
        mailbox_avaliador = recipes.mailbox_avaliador_inscricao.make()
        self.assertFalse(
            mailbox_avaliador.possui_inscricao_pendente(
                fase=mailbox_avaliador.fase,
                avaliador=mailbox_avaliador.avaliador
            )
        )

    def test_property_possui_inscricao_pendente_deve_retornar_true_se_mailbox_possuir_inscricoes_nao_avaliadas(
            self
    ):
        self.mailbox_avaliador.inscricoes.add(self.inscricaopreanalise)
        self.assertTrue(
            self.mailbox_avaliador.possui_inscricao_pendente(
                fase=self.mailbox_avaliador.fase,
                avaliador=self.mailbox_avaliador.avaliador
            )
        )

    def test_property_possui_inscricao_pendente_deve_retornar_true_se_mailbox_possuir_avaliacoes_nao_concluidas(
            self
    ):
        self.mailbox_avaliador.inscricoes.add(self.inscricaopreanalise)
        recipes.avaliacao_avaliador.make(
            inscricao=self.inscricaopreanalise,
            avaliador=self.mailbox_avaliador.avaliador,
            concluida=models.Concluida.NAO.name
        )
        self.assertTrue(
            self.mailbox_avaliador.possui_inscricao_pendente(
                fase=self.mailbox_avaliador.fase,
                avaliador=self.mailbox_avaliador.avaliador
            )
        )

    def test_property_possui_inscricao_pendente_deve_retornar_false_se_mailbox_possuir_avaliacoes_concluidas(
            self
    ):
        self.mailbox_avaliador.inscricoes.add(self.inscricaopreanalise)
        recipes.avaliacao_avaliador.make(
            inscricao=self.inscricaopreanalise,
            avaliador=self.mailbox_avaliador.avaliador,
            concluida=models.Concluida.SIM.name
        )
        self.assertFalse(
            self.mailbox_avaliador.possui_inscricao_pendente(
                fase=self.mailbox_avaliador.fase,
                avaliador=self.mailbox_avaliador.avaliador
            )
        )


class MailBoxHomologadorInscricaoTestCase(mixins.CursoTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.AvaliadorPSCT().sync()
        cls.mailbox_homologador = recipes.mailbox_homologador_inscricao.make()
        cls.inscricaopreanalise = recipes.inscricao_pre_analise.make(
            fase=cls.mailbox_homologador.fase,
            curso=cls.curso,
        )

    def test_str_deve_conter_avaliador(self):
        self.assertEqual(
            f"Caixa de Inscrições do Homologador {self.mailbox_homologador.homologador}",
            str(self.mailbox_homologador)
        )

    def test_property_possui_inscricao_pendente_deve_retornar_false_se_mailbox_estiver_vazia(self):
        mailbox_homologador = recipes.mailbox_homologador_inscricao.make()
        self.assertFalse(
            mailbox_homologador.possui_inscricao_pendente(
                fase=mailbox_homologador.fase,
                homologador=mailbox_homologador.homologador
            )
        )

    def test_property_possui_inscricao_pendente_deve_retornar_true_se_mailbox_possuir_inscricoes_nao_homologadas(
            self
    ):
        self.mailbox_homologador.inscricoes.add(self.inscricaopreanalise)
        self.assertTrue(
            self.mailbox_homologador.possui_inscricao_pendente(
                fase=self.mailbox_homologador.fase,
                homologador=self.mailbox_homologador.homologador
            )
        )

    def test_property_possui_inscricao_pendente_deve_retornar_false_se_mailbox_possuir_inscricoes_homologadas(
            self
    ):
        self.mailbox_homologador.inscricoes.add(self.inscricaopreanalise)
        recipes.avaliacao_homologador.make(
            inscricao=self.inscricaopreanalise,
            homologador=self.mailbox_homologador.homologador,
        )
        self.assertFalse(
            self.mailbox_homologador.possui_inscricao_pendente(
                fase=self.mailbox_homologador.fase,
                homologador=self.mailbox_homologador.homologador
            )
        )


class JustificativaIndeferimentoTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.justificativa_indeferimento = recipes.justificativa_indeferimento.make()

    def test_str_deve_conter_justificativa_do_indeferimento(self):
        self.assertEqual(
            self.justificativa_indeferimento.texto,
            str(self.justificativa_indeferimento)
        )


class AvaliacaoAvaliadorTestCase(mixins.CursoTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.AvaliadorPSCT().sync()
        cls.inscricao_pre_analise = recipes.inscricao_pre_analise.make(curso=cls.curso)
        cls.avaliacao_avaliador = recipes.avaliacao_avaliador.make(
            inscricao=cls.inscricao_pre_analise
        )

    def test_str_deve_conter_avaliador_e_inscricao_avaliada(self):
        self.assertEqual(
            (
                f"Avaliação (avaliador) de {self.avaliacao_avaliador.avaliador} "
                f"da {self.avaliacao_avaliador.inscricao}"
            ),
            str(self.avaliacao_avaliador)
        )

    def test_property_is_concluida_deve_retornar_false_se_avaliacao_nao_estiver_concluida(self):
        inscricao_pre_analise = recipes.inscricao_pre_analise.make(
            curso=self.curso
        )
        avaliacao_avaliador = recipes.avaliacao_avaliador.make(
            inscricao=inscricao_pre_analise,
            concluida=models.Concluida.NAO.name
        )
        self.assertFalse(avaliacao_avaliador.is_concluida)

    def test_property_is_concluida_deve_retornar_true_se_avaliacao_estiver_concluida(self):
        self.assertTrue(self.avaliacao_avaliador.is_concluida)

    def test_method_is_owner_deve_retornar_false_quando_usuario_nao_for_avaliador(self):
        user = base.tests.recipes.user.make()
        self.assertFalse(self.avaliacao_avaliador.is_owner(user=user))

    def test_method_is_owner_deve_retornar_true_quando_usuario_for_avaliador(self):
        self.assertTrue(self.avaliacao_avaliador.is_owner(user=self.avaliacao_avaliador.avaliador))

    @mock.patch("psct.models.AvaliacaoAvaliador.is_concluida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.AvaliacaoAvaliador.is_owner")
    def test_method_pode_alterar_deve_retornar_true(
            self, is_owner, acontecendo, is_concluida
    ):
        is_owner.return_value = True
        acontecendo.return_value = True
        is_concluida.return_value = False
        self.assertTrue(self.avaliacao_avaliador.pode_alterar(user=mock.Mock()))

    @mock.patch("psct.models.AvaliacaoAvaliador.is_concluida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.AvaliacaoAvaliador.is_owner")
    def test_method_pode_alterar_deve_retornar_false_quando_usuario_nao_for_avaliador(
            self, is_owner, acontecendo, is_concluida
    ):
        is_owner.return_value = False
        acontecendo.return_value = True
        is_concluida.return_value = False
        self.assertFalse(self.avaliacao_avaliador.pode_alterar(user=mock.Mock()))

    @mock.patch("psct.models.AvaliacaoAvaliador.is_concluida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.AvaliacaoAvaliador.is_owner")
    def test_method_pode_alterar_deve_retornar_false_quando_fase_nao_estiver_acontecendo(
            self, is_owner, acontecendo, is_concluida
    ):
        is_owner.return_value = True
        acontecendo.return_value = False
        is_concluida.return_value = False
        self.assertFalse(self.avaliacao_avaliador.pode_alterar(user=mock.Mock()))

    @mock.patch("psct.models.AvaliacaoAvaliador.is_concluida", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.AvaliacaoAvaliador.is_owner")
    def test_method_pode_alterar_deve_retornar_false_quando_inscricao_estiver_concluida(
            self, is_owner, acontecendo, is_concluida
    ):
        is_owner.return_value = True
        acontecendo.return_value = True
        is_concluida.return_value = True
        self.assertFalse(self.avaliacao_avaliador.pode_alterar(user=mock.Mock()))

    def test_method_save_deve_incrementar_progresso_de_analise_quando_for_nova_avaliacao(self):
        inscricao_pre_analise = recipes.inscricao_pre_analise.make(
            curso=self.curso
        )
        recipes.progresso_analise.make(
            fase=inscricao_pre_analise.fase,
            curso=inscricao_pre_analise.curso,
            modalidade=inscricao_pre_analise.modalidade,
        )
        avaliacao_avaliador = models.AvaliacaoAvaliador(
            inscricao=inscricao_pre_analise,
            situacao=models.SituacaoAvaliacao.DEFERIDA.name,
            avaliador=base.tests.recipes.user.make(),
            concluida=models.Concluida.NAO.name
        )
        avaliacao_avaliador.save()
        self.assertEqual(
            1,
            models.ProgressoAnalise.objects.filter(
                fase=inscricao_pre_analise.fase,
                curso=inscricao_pre_analise.curso,
                modalidade=inscricao_pre_analise.modalidade,
            ).count()
        )

    def test_method_save_deve_atualizar_deferimento_inscricao(self):
        inscricao_pre_analise = recipes.inscricao_pre_analise.make(
            curso=self.curso
        )
        avaliacao_avaliador = models.AvaliacaoAvaliador(
            inscricao=inscricao_pre_analise,
            situacao=models.SituacaoAvaliacao.DEFERIDA.name,
            avaliador=base.tests.recipes.user.make(),
            concluida=models.Concluida.SIM.name
        )
        avaliacao_avaliador.save()
        self.assertEqual(
            models.SituacaoInscricao.DEFERIDA.name,
            inscricao_pre_analise.situacao,
        )

    def test_method_save_deve_atualizar_indeferimento_inscricao(self):
        inscricao_pre_analise = recipes.inscricao_pre_analise.make(
            curso=self.curso
        )
        avaliacao_avaliador = models.AvaliacaoAvaliador(
            inscricao=inscricao_pre_analise,
            situacao=models.SituacaoAvaliacao.INDEFERIDA.name,
            avaliador=base.tests.recipes.user.make(),
            concluida=models.Concluida.SIM.name,
            texto_indeferimento=recipes.justificativa_indeferimento.make()
        )
        avaliacao_avaliador.save()
        self.assertEqual(
            models.SituacaoInscricao.INDEFERIDA.name,
            inscricao_pre_analise.situacao,
        )

    def test_method_save_deve_atualizar_situacao_inscricao_para_aguardando_homologador(self):
        fase_analise = recipes.fase_analise.make(
            quantidade_avaliadores=2,
            requer_homologador=True,
        )
        inscricao_pre_analise = recipes.inscricao_pre_analise.make(
            curso=self.curso, fase=fase_analise
        )
        avaliacao_a = recipes.avaliacao_avaliador_indeferida.make(inscricao=inscricao_pre_analise)
        avaliacao_b = models.AvaliacaoAvaliador(
            inscricao=inscricao_pre_analise,
            situacao=models.SituacaoAvaliacao.DEFERIDA.name,
            avaliador=base.tests.recipes.user.make(),
            concluida=models.Concluida.SIM.name,
        )
        avaliacao_b.save()
        self.assertEqual(
            models.SituacaoInscricao.AGUARDANDO_HOMOLOGADOR.name,
            inscricao_pre_analise.situacao,
        )


class AvaliacaoHomologadorTestCase(mixins.CursoTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.AvaliadorPSCT().sync()
        cls.inscricao_pre_analise = recipes.inscricao_pre_analise.make(curso=cls.curso)
        cls.avaliacao_homologador = recipes.avaliacao_homologador.make(
            inscricao=cls.inscricao_pre_analise
        )

    def test_str_deve_conter_homologador_e_inscricao_homologada(self):
        self.assertEqual(
            (
                f"Avaliação (homologador) de {self.avaliacao_homologador.homologador} "
                f"da {self.avaliacao_homologador.inscricao}"
            ),
            str(self.avaliacao_homologador)
        )

    def test_method_is_owner_deve_retornar_false_quando_usuario_nao_for_homologador(self):
        user = base.tests.recipes.user.make()
        self.assertFalse(self.avaliacao_homologador.is_owner(user=user))

    def test_method_is_owner_deve_retornar_true_quando_usuario_for_homologador(self):
        self.assertTrue(
            self.avaliacao_homologador.is_owner(user=self.avaliacao_homologador.homologador)
        )

    @mock.patch("psct.models.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.AvaliacaoHomologador.is_owner")
    def test_method_pode_alterar_deve_retornar_true(self, is_owner, acontecendo):
        is_owner.return_value = True
        acontecendo.return_value = True
        self.assertTrue(self.avaliacao_homologador.pode_alterar(user=mock.Mock()))

    @mock.patch("psct.models.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.AvaliacaoHomologador.is_owner")
    def test_method_pode_alterar_deve_retornar_false_quando_usuario_nao_for_homologador(
            self, is_owner, acontecendo
    ):
        is_owner.return_value = False
        acontecendo.return_value = True
        self.assertFalse(self.avaliacao_homologador.pode_alterar(user=mock.Mock()))

    @mock.patch("psct.models.FaseAnalise.acontecendo", new_callable=mock.PropertyMock)
    @mock.patch("psct.models.AvaliacaoHomologador.is_owner")
    def test_method_pode_alterar_deve_retornar_false_quando_fase_nao_estiver_acontecendo(
            self, is_owner, acontecendo
    ):
        is_owner.return_value = True
        acontecendo.return_value = False
        self.assertFalse(self.avaliacao_homologador.pode_alterar(user=mock.Mock()))

    def test_method_save_deve_atualizar_deferimento_inscricao(self):
        inscricao_pre_analise = recipes.inscricao_pre_analise.make(
            curso=self.curso
        )
        avaliacao_homologador = models.AvaliacaoHomologador(
            inscricao=inscricao_pre_analise,
            situacao=models.SituacaoAvaliacao.DEFERIDA.name,
            homologador=base.tests.recipes.user.make()
        )
        avaliacao_homologador.save()
        self.assertEqual(
            models.SituacaoInscricao.DEFERIDA.name,
            inscricao_pre_analise.situacao,
        )

    def test_method_save_deve_atualizar_indeferimento_inscricao(self):
        inscricao_pre_analise = recipes.inscricao_pre_analise.make(
            curso=self.curso
        )
        avaliacao_homologador = models.AvaliacaoHomologador(
            inscricao=inscricao_pre_analise,
            situacao=models.SituacaoAvaliacao.INDEFERIDA.name,
            homologador=base.tests.recipes.user.make(),
            texto_indeferimento=recipes.justificativa_indeferimento.make()
        )
        avaliacao_homologador.save()
        self.assertEqual(
            models.SituacaoInscricao.INDEFERIDA.name,
            inscricao_pre_analise.situacao,
        )


class GetLoteAvaliadorTestCase(
    mixins.FaseAnaliseTestData,
    mixins.ProcessoInscricaoMixin,
    TestCase
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.avaliador = cls.grupo_avaliadores.grupo.user_set.first()

    def setUp(self):
        super().setUp()
        self.total_inscricoes = 5
        self.inscricoes = recipes.inscricao_pre_analise.make(
            fase=self.fase_analise,
            curso=self.curso_tecnico,
            modalidade=self.modalidade_ampla,
            situacao=models.SituacaoInscricao.SEM_AVALIADORES.name,
            _quantity=self.total_inscricoes
        )

    def test_cria_mailbox_avaliador_inscricao(self):
        self.assertFalse(self.avaliador.mailbox_avaliador_inscricao.exists())
        models.get_lote_avaliador(self.fase_analise, self.avaliador, 0)
        self.assertTrue(self.avaliador.mailbox_avaliador_inscricao.exists())

    def test_obter_pacote_inscricoes_vazio(self):
        models.get_lote_avaliador(self.fase_analise, self.avaliador, 0)
        mailbox_avaliador = self.avaliador.mailbox_avaliador_inscricao.get(fase=self.fase_analise)
        self.assertEquals(0, mailbox_avaliador.inscricoes.count())

    def test_obter_pacote_inscricoes_com_inscricoes_disponiveis(self):
        quantidade_menor_que_total = self.total_inscricoes - 1
        models.get_lote_avaliador(self.fase_analise, self.avaliador, quantidade_menor_que_total)
        mailbox_avaliador = self.avaliador.mailbox_avaliador_inscricao.get(fase=self.fase_analise)
        self.assertEquals(
            quantidade_menor_que_total,
            mailbox_avaliador.inscricoes.count()
        )

    def test_obter_pacote_inscricoes_sem_inscricoes_disponiveis(self):
        models.get_lote_avaliador(self.fase_analise, self.avaliador, self.total_inscricoes)
        mailbox_avaliador = self.avaliador.mailbox_avaliador_inscricao.get(fase=self.fase_analise)
        quantidade_inscricoes_na_mailbox = mailbox_avaliador.inscricoes.count()

        models.get_lote_avaliador(self.fase_analise, self.avaliador, 1)
        self.assertEquals(
            quantidade_inscricoes_na_mailbox,
            mailbox_avaliador.inscricoes.count()
        )

    def test_obter_pacote_inscricoes_com_quantidade_menor_disponivel(self):
        quantidade_disponivel = self.total_inscricoes
        quantidade_maior_que_disponivel = quantidade_disponivel + 1
        models.get_lote_avaliador(
            self.fase_analise,
            self.avaliador,
            quantidade_maior_que_disponivel
        )
        mailbox_avaliador = self.avaliador.mailbox_avaliador_inscricao.get(fase=self.fase_analise)
        self.assertEquals(
            quantidade_disponivel,
            mailbox_avaliador.inscricoes.count()
        )


class GetLoteHomologadorTestCase(
    mixins.FaseAnaliseTestData,
    mixins.ProcessoInscricaoMixin,
    TestCase
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.homologador = cls.grupo_homologadores.grupo.user_set.first()

        cls.fase_analise.quantidade_avaliadores = 2
        cls.fase_analise.save()

    def setUp(self):
        super().setUp()
        self.total_inscricoes = 5
        self.inscricoes = recipes.inscricao_pre_analise.make(
            fase=self.fase_analise,
            curso=self.curso_tecnico,
            modalidade=self.modalidade_ampla,
            situacao=models.SituacaoInscricao.SEM_AVALIADORES.name,
            _quantity=self.total_inscricoes
        )
        for inscricao in self.inscricoes:
            recipes.avaliacao_avaliador.make(inscricao=inscricao)
            recipes.avaliacao_avaliador_indeferida.make(inscricao=inscricao)

    def test_cria_mailbox_homologador_inscricao(self):
        self.assertFalse(self.homologador.mailbox_homologador_inscricao.exists())
        models.get_lote_homologador(self.fase_analise, self.homologador, 0)
        self.assertTrue(self.homologador.mailbox_homologador_inscricao.exists())

    def test_obter_pacote_inscricoes_vazio(self):
        models.get_lote_homologador(self.fase_analise, self.homologador, 0)
        mailbox_homologador = self.homologador.mailbox_homologador_inscricao.get(
            fase=self.fase_analise
        )
        self.assertEquals(0, mailbox_homologador.inscricoes.count())

    def test_obter_pacote_inscricoes_com_inscricoes_disponiveis(self):
        quantidade_menor_que_total = self.total_inscricoes - 1
        models.get_lote_homologador(self.fase_analise, self.homologador, quantidade_menor_que_total)
        mailbox_homologador = self.homologador.mailbox_homologador_inscricao.get(
            fase=self.fase_analise
        )
        self.assertEquals(
            quantidade_menor_que_total,
            mailbox_homologador.inscricoes.count()
        )

    def test_obter_pacote_inscricoes_sem_inscricoes_disponiveis(self):
        models.get_lote_homologador(self.fase_analise, self.homologador, self.total_inscricoes)
        mailbox_homologador = self.homologador.mailbox_homologador_inscricao.get(
            fase=self.fase_analise
        )
        quantidade_inscricoes_na_mailbox = mailbox_homologador.inscricoes.count()

        models.get_lote_homologador(self.fase_analise, self.homologador, 1)
        self.assertEquals(
            quantidade_inscricoes_na_mailbox,
            mailbox_homologador.inscricoes.count()
        )

    def test_obter_pacote_inscricoes_com_quantidade_menor_disponivel(self):
        quantidade_disponivel = self.total_inscricoes
        quantidade_maior_que_disponivel = quantidade_disponivel + 1
        models.get_lote_homologador(
            self.fase_analise,
            self.homologador,
            quantidade_maior_que_disponivel
        )
        mailbox_homologador = self.homologador.mailbox_homologador_inscricao.get(
            fase=self.fase_analise
        )
        self.assertEquals(
            quantidade_disponivel,
            mailbox_homologador.inscricoes.count()
        )
