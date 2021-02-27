from datetime import date
from unittest.mock import patch, PropertyMock

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from freezegun import freeze_time
from model_mommy import mommy

import base.tests.recipes
import candidatos.permissions
from base.cleaners import remove_simbolos_cpf
from cursos.tests.mixins import DiretorEnsinoPermissionData
from editais.choices import EventoCronogramaChoices
from . import recipes
from .. import models


class EtapaCleanTestCase(DiretorEnsinoPermissionData, TestCase):
    def test_deveria_bloquear_quando_edicao_nao_possui_dados_importados(self):
        edicao = recipes.edicao.make(importado=False)
        etapa = models.Etapa(edicao=edicao)
        with self.assertRaises(ValidationError) as ex:
            etapa.clean()

        self.assertIn(
            "Esta edição não possui dados de candidatos importados.",
            ex.exception.message_dict["edicao"],
        )

    def test_deveria_bloquear_quando_houver_etapa_aberta(self):
        edicao = recipes.edicao.make(importado=True)
        etapa = recipes.etapa.make(edicao=edicao)  # Etapa aberta
        nova_etapa = models.Etapa(edicao=edicao)
        with self.assertRaises(ValidationError) as ex:
            nova_etapa.clean()

        self.assertIn(
            "Existe outra etapa aberta para esta edição. Você deve encerrá-la antes de continuar.",
            ex.exception.messages,
        )

    def test_deveria_bloquear_com_campus_vazio_e_a_edicao_possuir_etapa_de_campus(self):
        campus = mommy.make("cursos.Campus")
        edicao = recipes.edicao.make(importado=True)
        etapa = recipes.etapa.make(campus=campus, edicao=edicao)
        nova_etapa = models.Etapa(edicao=etapa.edicao)
        with self.assertRaises(ValidationError) as ex:
            nova_etapa.clean()

        self.assertIn(
            "Você não pode criar uma etapa sistêmica, pois já existe etapa de campus criada para esta edição.",
            ex.exception.messages,
        )

    def test_deveria_bloquear_com_multiplicador_diferente_de_um(self):
        edicao = recipes.edicao.make(importado=True)
        etapa = models.Etapa(edicao=edicao, multiplicador=2, numero=0)
        with self.assertRaises(ValidationError) as ex:
            etapa.clean()

        self.assertIn(
            "A etapa de resultado não pode ter multiplicador diferente de 1",
            ex.exception.messages,
        )

    def test_deveria_bloquear_encerramento_quando_houver_interesses_nao_analisados(
        self,
    ):
        edicao = recipes.edicao.make(importado=True)
        etapa = recipes.etapa.make(encerrada=True, edicao=edicao)
        recipes.confirmacao.make(etapa=etapa)
        mommy.make(
            "editais.PeriodoConvocacao",
            evento=EventoCronogramaChoices.ANALISE.name,
            etapa=etapa,
            gerenciavel=True,
        )
        with self.assertRaises(ValidationError) as ex:
            etapa.clean()

        self.assertIn(
            "Há confirmações de interesses que não foram analisadas:",
            ex.exception.messages[0],
        )


class EtapaTestCase(DiretorEnsinoPermissionData, TestCase):
    fixtures = ["modalidade.json"]

    def test_etapa_pode_ser_encerrada(self):
        etapa = recipes.etapa.make()
        self.assertTrue(etapa.pode_encerrar())

    def test_etapa_nao_pode_ser_encerrada(self):
        etapa = recipes.etapa.make()
        recipes.confirmacao.make(etapa=etapa)
        mommy.make(
            "editais.PeriodoConvocacao",
            evento=EventoCronogramaChoices.ANALISE.name,
            etapa=etapa,
            gerenciavel=True,
        )
        self.assertFalse(etapa.pode_encerrar())

    def test_etapa_pode_ser_reaberta(self):
        etapa = recipes.etapa.make(encerrada=True)
        self.assertTrue(etapa.pode_reabrir())

    def test_etapa_nao_pode_ser_reaberta_quando_nao_eh_a_ultima_etapa(self):
        etapa = recipes.etapa.make(encerrada=True)
        recipes.etapa.make(edicao=etapa.edicao, encerrada=True)
        self.assertFalse(etapa.pode_reabrir())

    def test_etapa_nao_pode_ser_reaberta_quando_nao_esta_encerrada(self):
        etapa = recipes.etapa.make()
        self.assertFalse(etapa.pode_reabrir())

    def test_etapa_deveria_gerar_chamadas_no_campus_a(self):
        curso_campus_a = mommy.make(
            "cursos.CursoSelecao",
        )
        curso__campus_b = mommy.make(
            "cursos.CursoSelecao",
        )
        etapa = recipes.etapa.make(multiplicador=1, campus=curso_campus_a.campus)
        modalidade = models.Modalidade.objects.get(
            pk=models.ModalidadeEnum.ampla_concorrencia
        )
        recipes.vaga.make(
            curso=curso_campus_a, edicao=etapa.edicao, modalidade=modalidade
        )
        recipes.vaga.make(
            curso=curso__campus_b, edicao=etapa.edicao, modalidade=modalidade
        )
        etapa.gerar_chamadas()
        self.assertTrue(models.Chamada.objects.filter(curso=curso_campus_a).exists())

    def test_etapa_nao_deveria_gerar_chamadas_no_campus_b(self):
        curso_campus_a = mommy.make(
            "cursos.CursoSelecao",
        )
        curso__campus_b = mommy.make(
            "cursos.CursoSelecao",
        )
        etapa = recipes.etapa.make(multiplicador=1, campus=curso_campus_a.campus)
        modalidade = models.Modalidade.objects.get(
            pk=models.ModalidadeEnum.ampla_concorrencia
        )
        recipes.vaga.make(
            curso=curso_campus_a, edicao=etapa.edicao, modalidade=modalidade
        )
        recipes.vaga.make(
            curso=curso__campus_b, edicao=etapa.edicao, modalidade=modalidade
        )
        etapa.gerar_chamadas()
        self.assertFalse(models.Chamada.objects.filter(curso=curso__campus_b).exists())

    def test_etapa_deveria_gerar_chamadas_em_todos_os_campus(self):
        etapa = recipes.etapa.make(multiplicador=1)
        curso_campus_a = mommy.make(
            "cursos.CursoSelecao",
        )
        curso__campus_b = mommy.make(
            "cursos.CursoSelecao",
        )
        modalidade = models.Modalidade.objects.get(
            pk=models.ModalidadeEnum.ampla_concorrencia
        )
        recipes.vaga.make(
            curso=curso_campus_a, edicao=etapa.edicao, modalidade=modalidade
        )
        recipes.vaga.make(
            curso=curso__campus_b, edicao=etapa.edicao, modalidade=modalidade
        )
        etapa.gerar_chamadas()
        self.assertTrue(models.Chamada.objects.filter(curso=curso_campus_a).exists())
        self.assertTrue(models.Chamada.objects.filter(curso=curso__campus_b).exists())

    def test_deveria_remover_resultados_ao_reabrir_etapa(self):
        resultado = recipes.resultado.make()
        resultado.etapa.reabrir()
        self.assertFalse(models.Resultado.objects.exists())

    def test_deveria_desmatricular_candidatos_ao_reabrir_etapa(self):
        resultado = recipes.resultado.make()
        vaga = recipes.vaga.make(
            edicao=resultado.etapa.edicao,
            candidato=resultado.inscricao.candidato,
            curso=resultado.inscricao.curso,
            modalidade=resultado.inscricao.modalidade,
        )
        resultado.etapa.reabrir()
        vaga_atualizada = models.Vaga.objects.get(id=vaga.id)
        self.assertIsNone(vaga_atualizada.candidato)

    def test_nao_deveria_mover_analise_e_confirmacao_quando_existe_confirmacao_ampla(self):
        confirmacao = recipes.confirmacao.make()
        modalidade_cota = models.Modalidade.objects.get(pk=models.ModalidadeEnum.cota_racial)
        inscricao_cota = recipes.inscricao.make(candidato=confirmacao.inscricao.candidato, modalidade=modalidade_cota)
        with self.assertRaises(models.ConfirmacaoInteresse.Error) as ex:
            confirmacao.etapa.mover_analise_e_confirmacao(
                inscricao_cota, confirmacao.inscricao
            )

        self.assertIn(
            "Confirmação de interesse já existe na ampla concorrência.",
            ex.exception.args,
        )

    def test_deveria_mover_analise_e_confirmacao_quando_existe_nao_existe_confirmacao_ampla(self):
        confirmacao = recipes.confirmacao.make()
        inscricao = recipes.inscricao.make()
        confirmacao.etapa.mover_analise_e_confirmacao(confirmacao.inscricao, inscricao)
        confirmacao_atualizada = models.ConfirmacaoInteresse.objects.get(
            id=confirmacao.id
        )
        self.assertEqual(confirmacao_atualizada.inscricao, inscricao)

    def test_deveriar_retornar_status_deferido(self):
        analise = recipes.analise.make()
        etapa = analise.confirmacao_interesse.etapa
        expected = "DEFERIDO", "Observação"
        self.assertEqual(
            expected, etapa._verificar_status(analise, "DEFERIDO", "Observação")
        )

    def test_deveriar_retornar_status_indeferido_com_observacao_da_analise(self):
        analise = recipes.analise.make(situacao_final=False, observacao="Observação")
        etapa = analise.confirmacao_interesse.etapa
        expected = "INDEFERIDO", "DOCUMENTAÇÃO INVÁLIDA - OBSERVAÇÃO"
        self.assertEqual(expected, etapa._verificar_status(analise, None, None))

    def test_deveriar_retornar_status_do_recurso_da_analise(self):
        analise = recipes.analise.make(situacao_final=False)
        recipes.recurso.make(
            analise_documental=analise,
            status_recurso="INDEFERIDO",
            justificativa="Alguma justificativa",
        )
        etapa = analise.confirmacao_interesse.etapa
        expected = "INDEFERIDO", "RECURSO INDEFERIDO - ALGUMA JUSTIFICATIVA"
        self.assertEqual(expected, etapa._verificar_status(analise, None, None))


class EncerramentoEtapaTestCase(DiretorEnsinoPermissionData, TestCase):
    fixtures = ["modalidade.json"]

    def setUp(self) -> None:
        super().setUp()

        self.chamada = recipes.chamada.make(multiplicador=2)
        self.inscricao = recipes.inscricao.make(
            chamada=self.chamada,
            edicao=self.chamada.etapa.edicao,
            modalidade=self.chamada.modalidade,
            curso=self.chamada.curso,
        )
        recipes.vaga.make(
            modalidade=self.chamada.modalidade,
            edicao=self.chamada.etapa.edicao,
            curso=self.chamada.curso,
        )

    def test_deveria_bloquear_encerrar_etapa_ja_encerrada(self):
        etapa = recipes.etapa.make(encerrada=True)
        with self.assertRaises(models.Etapa.Error) as ex:
            etapa.encerrar()

        self.assertIn("Etapa já encerrada", ex.exception.args)

    def test_resultado_deveria_ser_deferido_dentro_das_vagas_em_etapa(self):
        recipes.confirmacao.make(etapa=self.chamada.etapa, inscricao=self.inscricao)
        self.chamada.etapa.encerrar()
        resultado = models.Resultado.objects.filter(
            inscricao=self.inscricao, etapa=self.chamada.etapa
        ).first()
        self.assertEqual("DEFERIDO", resultado.status)
        self.assertEqual("CANDIDATO APTO A REALIZAR MATRÍCULA", resultado.observacao)

    def test_resultado_deveriar_ser_excedente_em_etapa(self):
        inscricao = recipes.inscricao.make(
            chamada=self.chamada,
            edicao=self.chamada.etapa.edicao,
            modalidade=self.chamada.modalidade,
            curso=self.chamada.curso,
        )
        recipes.desempenho.make(inscricao=self.inscricao, classificacao=1)
        recipes.desempenho.make(inscricao=inscricao, classificacao=2)
        recipes.confirmacao.make(etapa=self.chamada.etapa, inscricao=self.inscricao)
        recipes.confirmacao.make(etapa=self.chamada.etapa, inscricao=inscricao)
        self.chamada.etapa.encerrar()
        resultado = models.Resultado.objects.get(
            etapa=self.chamada.etapa, inscricao=inscricao
        )
        self.assertEqual("EXCEDENTE", resultado.status)
        self.assertEqual("CANDIDATO NA LISTA DE ESPERA", resultado.observacao)

    def test_nao_deveria_criar_resultado_sem_documentacao_em_etapa(self):
        mommy.make(
            "editais.PeriodoConvocacao",
            evento=EventoCronogramaChoices.ANALISE.name,
            etapa=self.chamada.etapa,
            gerenciavel=True,
        )
        self.chamada.etapa.encerrar()
        self.assertFalse(models.Resultado.objects.exists())

    def test_deveriar_criar_resultado_com_analise_de_documentacao_gerenciada_em_etapa(
        self,
    ):
        mommy.make(
            "editais.PeriodoConvocacao",
            evento=EventoCronogramaChoices.ANALISE.name,
            etapa=self.chamada.etapa,
            gerenciavel=True,
        )
        confirmacao = recipes.confirmacao.make(
            etapa=self.chamada.etapa, inscricao=self.inscricao
        )
        recipes.analise.make(confirmacao_interesse=confirmacao)
        self.chamada.etapa.encerrar()
        resultado = models.Resultado.objects.filter(
            inscricao=self.inscricao, etapa=self.chamada.etapa
        ).first()
        self.assertEqual("DEFERIDO", resultado.status)
        self.assertEqual("CANDIDATO APTO A REALIZAR MATRÍCULA", resultado.observacao)

    def test_resultado_deveriar_ser_deferido_para_cotista_com_vagas_nas_cotas(self):
        modalidade = models.Modalidade.objects.get(id=models.ModalidadeEnum.cota_racial)
        chamada = recipes.chamada.make(modalidade=modalidade)
        inscricao = recipes.inscricao.make(
            chamada=chamada,
            edicao=chamada.etapa.edicao,
            modalidade=modalidade,
            curso=chamada.curso,
        )
        recipes.vaga.make(
            modalidade=modalidade,
            edicao=chamada.etapa.edicao,
            curso=chamada.curso,
        )
        confirmacao = recipes.confirmacao.make(etapa=chamada.etapa, inscricao=inscricao)
        recipes.analise.make(confirmacao_interesse=confirmacao)
        chamada.etapa.encerrar()
        resultado = models.Resultado.objects.filter(
            inscricao=inscricao, etapa=chamada.etapa
        ).first()
        self.assertEqual("DEFERIDO", resultado.status)
        self.assertEqual("CANDIDATO APTO A REALIZAR MATRÍCULA", resultado.observacao)

    def test_resultado_deveriar_ser_indeferido_para_cotista_sem_vagas_nas_cotas(self):
        modalidade = models.Modalidade.objects.get(id=models.ModalidadeEnum.cota_racial)
        chamada = recipes.chamada.make(modalidade=modalidade, multiplicador=2)
        inscricao_a = recipes.inscricao.make(
            chamada=chamada,
            edicao=chamada.etapa.edicao,
            modalidade=modalidade,
            curso=chamada.curso,
        )
        inscricao_b = recipes.inscricao.make(
            chamada=chamada,
            edicao=chamada.etapa.edicao,
            modalidade=modalidade,
            curso=chamada.curso,
        )
        recipes.desempenho.make(inscricao=inscricao_a, classificacao=1)
        recipes.desempenho.make(inscricao=inscricao_b, classificacao=2)
        recipes.vaga.make(
            modalidade=modalidade,
            edicao=chamada.etapa.edicao,
            curso=chamada.curso,
        )
        confirmacao_a = recipes.confirmacao.make(
            etapa=chamada.etapa, inscricao=inscricao_a
        )
        confirmacao_b = recipes.confirmacao.make(
            etapa=chamada.etapa, inscricao=inscricao_b
        )
        recipes.analise.make(confirmacao_interesse=confirmacao_a)
        recipes.analise.make(confirmacao_interesse=confirmacao_b)
        chamada.etapa.encerrar()
        resultado = models.Resultado.objects.filter(
            inscricao=inscricao_b, etapa=chamada.etapa
        ).first()
        self.assertEqual("EXCEDENTE", resultado.status)
        self.assertEqual("CANDIDATO NA LISTA DE ESPERA", resultado.observacao)

    def test_nao_deveria_encerrar_etapa_com_quantidade_avaliacoes_diferentes_dos_tipos_de_analise(self):
        modalidade = models.Modalidade.objects.get(id=models.ModalidadeEnum.cota_racial)
        recipes.tipo_analise.make(modalidade=[modalidade])
        tipo_analise = recipes.tipo_analise.make(modalidade=[modalidade])
        chamada = recipes.chamada.make(modalidade=modalidade)
        inscricao = recipes.inscricao.make(
            chamada=chamada,
            edicao=chamada.etapa.edicao,
            modalidade=modalidade
        )
        confirmacao = recipes.confirmacao.make(inscricao=inscricao, etapa=chamada.etapa)
        analise = recipes.analise.make(confirmacao_interesse=confirmacao)
        recipes.avaliacao.make(analise_documental=analise, tipo_analise=tipo_analise)
        with self.assertRaises(models.Etapa.EncerrarEtapaError) as ex:
            chamada.etapa.encerrar()

        self.assertEqual(
            f"A inscricão do candidato {inscricao.candidato} possui quantidade de "
            "avaliações diferente dos tipos de análise da modalidade",
            ex.exception.messages[0]
        )

    def test_nao_deveria_encerrar_etapa_com_tipo_de_analise_diferentes_da_modalidade(self):
        modalidade = models.Modalidade.objects.get(id=models.ModalidadeEnum.cota_racial)
        recipes.tipo_analise.make(modalidade=[modalidade])
        chamada = recipes.chamada.make(modalidade=modalidade)
        inscricao = recipes.inscricao.make(
            chamada=chamada,
            edicao=chamada.etapa.edicao,
            modalidade=modalidade
        )
        confirmacao = recipes.confirmacao.make(inscricao=inscricao, etapa=chamada.etapa)
        analise = recipes.analise.make(confirmacao_interesse=confirmacao)
        recipes.avaliacao.make(analise_documental=analise)
        with self.assertRaises(models.Etapa.EncerrarEtapaError) as ex:
            chamada.etapa.encerrar()

        self.assertEqual(
            f"A inscrição do candidato {inscricao.candidato} possui avaliação "
            "inexistente nos tipos de análise da cota",
            ex.exception.messages[0]
        )


class ChamadaCleanTestCase(DiretorEnsinoPermissionData, TestCase):
    def test_deveria_bloquear_criar_chamada_com_mesmas_informacoes(self):
        chamada = recipes.chamada.make()
        nova_chamada = models.Chamada(
            etapa=chamada.etapa, modalidade=chamada.modalidade, curso=chamada.curso
        )
        with self.assertRaises(ValidationError) as ex:
            nova_chamada.clean()

        self.assertIn(
            "Essa chamada já foi inserida",
            ex.exception.messages,
        )

    def test_deveria_bloquear_criar_chamada_com_etapa_ja_encerrada(self):
        etapa = recipes.etapa.make(encerrada=True)
        chamada = recipes.chamada.make(etapa=etapa)
        with self.assertRaises(ValidationError) as ex:
            chamada.clean()

        self.assertIn(
            "A etapa já foi encerrada!",
            ex.exception.messages,
        )

    def test_deveria_bloquear_criar_chamada_de_resultado_com_multiplicador_diferente_de_um(
        self,
    ):
        etapa = recipes.etapa.make(numero=0)
        chamada = recipes.chamada.make(etapa=etapa, multiplicador=2)
        with self.assertRaises(ValidationError) as ex:
            chamada.clean()

        self.assertIn(
            "A chamada de resultado não pode ter multiplicado maior que 1",
            ex.exception.messages,
        )


class ChamadaTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        candidatos.permissions.Candidatos().sync()
        cls.chamada = recipes.chamada.make()
        recipes.vaga.make(
            modalidade=cls.chamada.modalidade,
            edicao=cls.chamada.etapa.edicao,
            curso=cls.chamada.curso,
        )
        cls.inscricao = recipes.inscricao.make(
            chamada=cls.chamada,
            edicao=cls.chamada.etapa.edicao,
            curso=cls.chamada.curso,
            modalidade=cls.chamada.modalidade,
        )

    def test_nao_deveriar_existir_inscricoes_na_chamada(self):
        chamada = recipes.chamada.make()
        recipes.vaga.make(
            modalidade=chamada.modalidade,
            edicao=chamada.etapa.edicao,
            curso=chamada.curso,
        )
        chamada.adicionar_inscricoes()
        self.assertFalse(chamada.inscricoes.exists())

    @patch("processoseletivo.models.Chamada.criar_usuarios_pendentes")
    def test_deveriar_existir_as_inscricoes_dentro_das_vagas_na_chamada(self, method):
        method.return_value = None
        self.chamada.adicionar_inscricoes()
        self.assertIn(self.inscricao, self.chamada.inscricoes.all())

    @patch("processoseletivo.models.Chamada.criar_usuarios_pendentes")
    def test_nao_deveriar_existir_as_inscricoes_fora_das_vagas_na_chamada(self, method):
        method.return_value = None
        inscricao = recipes.inscricao.make(
            edicao=self.chamada.etapa.edicao,
            curso=self.chamada.curso,
            modalidade=self.chamada.modalidade,
        )
        self.chamada.adicionar_inscricoes()
        self.assertNotIn(inscricao, self.chamada.inscricoes.all())

    def test_deveriar_criar_usuario_inexistente_no_sistema(self):
        self.chamada.criar_usuarios_pendentes()
        cpf = remove_simbolos_cpf(self.inscricao.candidato.pessoa.cpf)
        self.assertTrue(User.objects.filter(username=cpf).exists())

    def test_deveriar_associar_usuario_ao_candidato_quando_existir_mesmo_cpf_no_sistema(
        self,
    ):
        user = base.tests.recipes.user.make(
            username=remove_simbolos_cpf(self.inscricao.candidato.pessoa.cpf)
        )
        self.chamada.criar_usuarios_pendentes()
        inscricao_atualizada = models.Inscricao.objects.get(id=self.inscricao.id)
        self.assertEqual(user, inscricao_atualizada.candidato.pessoa.user)


class EdicaoCleanTestCase(TestCase):
    def test_deveria_bloquear_criar_edicao_com_mesmas_informacoes(self):
        edicao = recipes.edicao.make()
        nova_edicao = models.Edicao(
            processo_seletivo=edicao.processo_seletivo,
            ano=edicao.ano,
            semestre=edicao.semestre,
            nome=edicao.nome,
        )
        with self.assertRaises(ValidationError) as ex:
            nova_edicao.clean()

        self.assertIn(
            "Já há uma edição de processo seletivo com as informações inseridas.",
            ex.exception.messages,
        )


class EdicaoTestCase(DiretorEnsinoPermissionData, TestCase):
    fixtures = ["modalidade.json"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.edicao = recipes.edicao.make(ano=date.today().year)
        curso = mommy.make("cursos.CursoSelecao")
        modalidade = models.Modalidade.objects.get(
            id=models.ModalidadeEnum.ampla_concorrencia
        )
        pessoa_a = base.tests.recipes.pessoa_fisica.make(
            nascimento=date(year=1992, month=3, day=25)
        )
        pessoa_b = base.tests.recipes.pessoa_fisica.make(
            nascimento=date(year=1992, month=3, day=26)
        )
        candidato_a = recipes.candidato.make(pessoa=pessoa_a)
        candidato_b = recipes.candidato.make(pessoa=pessoa_b)
        cls.inscricao_a = recipes.inscricao.make(
            modalidade=modalidade, curso=curso, edicao=cls.edicao, candidato=candidato_a
        )
        cls.inscricao_b = recipes.inscricao.make(
            chamada=cls.inscricao_a.chamada,
            edicao=cls.edicao,
            modalidade=modalidade,
            curso=curso,
            candidato=candidato_b,
        )

    def test_str_deveria_conter_sigla_e_ano(self):
        processo = recipes.processo_seletivo.make(sigla='PS')
        edicao = recipes.edicao.make(nome="", ano=2020, processo_seletivo=processo)
        self.assertEqual("PS 2020", str(edicao))

    def test_str_deveria_conter_sigla_ano_e_semestre(self):
        processo = recipes.processo_seletivo.make(sigla='PS')
        edicao = recipes.edicao.make(nome="", semestre=1, ano=2020, processo_seletivo=processo)
        self.assertEqual("PS 2020.1", str(edicao))

    def test_str_deveria_conter_sigla_ano_semestre_e_nome(self):
        processo = recipes.processo_seletivo.make(sigla='PS')
        edicao = recipes.edicao.make(
            nome="Novo PSCT", semestre=1, ano=2020, processo_seletivo=processo
        )
        self.assertEqual("PS 2020.1 - Novo PSCT", str(edicao))

    def test_deveria_definir_inscricao_a_em_primeiro_lugar_com_desempate_por_redacao(
        self,
    ):
        desempenho = recipes.desempenho.make(
            inscricao=self.inscricao_a, nota_geral=40, nota_na_redacao=10
        )
        recipes.desempenho.make(
            inscricao=self.inscricao_b, nota_geral=40, nota_na_redacao=9.9
        )
        self.edicao.definir_classificacoes()
        desempenho_atualizado = models.Desempenho.objects.get(id=desempenho.id)
        self.assertEqual(1, desempenho_atualizado.classificacao)

    def test_deveriar_definir_inscricao_b_em_segundo_lugar_com_desempate_por_redacao(
        self,
    ):
        recipes.desempenho.make(
            inscricao=self.inscricao_a, nota_geral=40, nota_na_redacao=10
        )
        desempenho = recipes.desempenho.make(
            inscricao=self.inscricao_b, nota_geral=40, nota_na_redacao=9.9
        )
        self.edicao.definir_classificacoes()
        desempenho_atualizado = models.Desempenho.objects.get(id=desempenho.id)
        self.assertEqual(2, desempenho_atualizado.classificacao)

    def test_deveriar_definir_inscricao_a_em_primeiro_lugar_com_desempate_por_idade(
        self,
    ):
        notas = {
            "nota_geral": 50,
            "nota_na_redacao": 10,
            "nota_em_linguas": 10,
            "nota_em_matematica": 10,
            "nota_em_ciencias_naturais": 10,
            "nota_em_humanas": 10,
        }
        desempenho = recipes.desempenho.make(inscricao=self.inscricao_a, **notas)
        recipes.desempenho.make(inscricao=self.inscricao_b, **notas)
        self.edicao.definir_classificacoes()
        desempenho_atualizado = models.Desempenho.objects.get(id=desempenho.id)
        self.assertEqual(1, desempenho_atualizado.classificacao)


class InscricaoTestCase(DiretorEnsinoPermissionData, TestCase):
    fixtures = ["modalidade.json"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.etapa = recipes.etapa.make()
        cls.ampla = models.Modalidade.objects.get(
            id=models.ModalidadeEnum.ampla_concorrencia
        )
        cls.chamada = recipes.chamada.make(etapa=cls.etapa, modalidade=cls.ampla)
        cls.inscricao = recipes.inscricao.make(
            edicao=cls.etapa.edicao, modalidade=cls.ampla, chamada=cls.chamada
        )

    def test_nao_deveria_matricular_candidato_ja_matriculado(self):
        recipes.matricula.make(etapa=self.etapa, inscricao=self.inscricao)
        with self.assertRaises(models.Matricula.Error) as ex:
            self.inscricao.matricular(self.etapa)

        self.assertIn("Candidato já matriculado", ex.exception.args)

    def test_nao_deveria_matricular_sem_vagas(self):
        with self.assertRaises(models.Matricula.Error) as ex:
            self.inscricao.matricular(self.etapa)

        self.assertIn("Sem vagas disponíveis", ex.exception.args)

    def test_deveria_matricular_em_vaga_disponivel(self):
        chamada = recipes.chamada.make(
            etapa=self.etapa,
            curso=self.inscricao.curso,
            modalidade=self.inscricao.modalidade,
        )
        recipes.vaga.make(
            modalidade=chamada.modalidade,
            edicao=self.etapa.edicao,
            curso=chamada.curso,
        )
        self.inscricao.matricular(self.etapa)
        self.assertIn(
            self.inscricao, models.Inscricao.objects.filter(matricula__isnull=False)
        )

    def test_nao_deveria_cancelar_matricula_de_candidato_nao_matriculado(self):
        with self.assertRaises(models.Matricula.Error) as ex:
            self.inscricao.cancelar_matricula(self.etapa)

        self.assertIn("Candidato não está matriculado", ex.exception.args)

    def test_deveria_cancelar_matricula(self):
        recipes.matricula.make(inscricao=self.inscricao, etapa=self.etapa)
        chamada = recipes.chamada.make(
            etapa=self.etapa,
            curso=self.inscricao.curso,
            modalidade=self.inscricao.modalidade,
        )
        recipes.vaga.make(
            modalidade=chamada.modalidade,
            edicao=self.etapa.edicao,
            curso=chamada.curso,
        )
        self.inscricao.cancelar_matricula(self.etapa)
        self.assertFalse(
            models.Matricula.objects.filter(inscricao=self.inscricao).exists()
        )
        self.assertIsNone(models.Vaga.objects.first().candidato)

    def test_deveria_retornar_situacao_none_quando_nao_houver_outra_inscricao(self):
        self.assertIsNone(
            self.inscricao.get_situacao_matricula_outra_chamada(self.etapa)
        )

    def test_deveria_retornar_matriculado_em_lista_geral(self):
        cota = models.Modalidade.objects.get(id=models.ModalidadeEnum.cota_racial)
        chamada = recipes.chamada.make(etapa=self.etapa, modalidade=cota)
        inscricao = recipes.inscricao.make(
            chamada=chamada,
            modalidade=cota,
            edicao=self.etapa.edicao,
            candidato=self.inscricao.candidato,
        )
        recipes.matricula.make(inscricao=self.inscricao)
        self.assertEqual(
            inscricao.get_situacao_matricula_outra_chamada(self.etapa),
            "Matriculado(a) na lista geral",
        )

    def test_deveria_retornar_matriculado_em_cota(self):
        cota = models.Modalidade.objects.get(id=models.ModalidadeEnum.cota_racial)
        chamada = recipes.chamada.make(etapa=self.etapa, modalidade=cota)
        inscricao = recipes.inscricao.make(
            chamada=chamada,
            modalidade=cota,
            edicao=self.etapa.edicao,
            candidato=self.inscricao.candidato,
        )
        recipes.matricula.make(inscricao=inscricao)
        self.assertEqual(
            self.inscricao.get_situacao_matricula_outra_chamada(self.etapa),
            "Matriculado(a) em Cota",
        )

    @patch("processoseletivo.models.Inscricao.get_situacao_matricula_outra_chamada")
    def test_deveria_retornar_situacao_da_matricula_em_outra_chamada(self, method):
        method.return_value = "Matriculado"
        self.assertEqual(
            self.inscricao.get_situacao_matricula_em_chamada(self.etapa), "Matriculado"
        )

    @patch("processoseletivo.models.Inscricao.get_situacao_matricula_outra_chamada")
    def test_deveria_retornar_hifen_para_situacao_da_matricula_etapa_nao_encerrada(
        self, method
    ):
        method.return_value = None
        self.assertEqual(
            self.inscricao.get_situacao_matricula_em_chamada(self.etapa), "-"
        )

    @patch("processoseletivo.models.Inscricao.get_situacao_matricula_outra_chamada")
    def test_deveria_retornar_situacao_matriculado(self, method):
        method.return_value = None
        etapa = recipes.etapa.make(encerrada=True)
        inscricao = recipes.inscricao.make(edicao=etapa.edicao)
        recipes.matricula.make(inscricao=inscricao, etapa=etapa)
        self.assertEqual(
            inscricao.get_situacao_matricula_em_chamada(etapa), "Matriculado(a)"
        )

    @patch("processoseletivo.models.Inscricao.get_situacao_matricula_outra_chamada")
    def test_deveria_retornar_situacao_lista_de_espera_com_confirmacao_interesse(
        self, method
    ):
        method.return_value = None
        etapa = recipes.etapa.make(encerrada=True)
        inscricao = recipes.inscricao.make(edicao=etapa.edicao)
        recipes.confirmacao.make(etapa=etapa, inscricao=inscricao)
        self.assertEqual(
            inscricao.get_situacao_matricula_em_chamada(etapa), "Lista de Espera"
        )

    @patch("processoseletivo.models.Inscricao.get_situacao_matricula_outra_chamada")
    @patch("processoseletivo.models.Inscricao.status_documentacao")
    @patch("processoseletivo.models.Etapa.analise_documentacao_gerenciada")
    def test_deveria_retornar_situacao_lista_de_espera_com_recurso_deferido(
        self, analise_documentacao, status_documentacao, situacao_matricula
    ):
        analise_documentacao.return_value = True
        status_documentacao.return_value = True
        situacao_matricula.return_value = None
        etapa = recipes.etapa.make(encerrada=True)
        inscricao = recipes.inscricao.make(edicao=etapa.edicao)
        confirmacao = recipes.confirmacao.make(etapa=etapa, inscricao=inscricao)
        analise = recipes.analise.make(confirmacao_interesse=confirmacao)
        recipes.recurso.make(analise_documental=analise)
        self.assertEqual(
            inscricao.get_situacao_matricula_em_chamada(etapa), "Lista de Espera"
        )

    @patch("processoseletivo.models.Inscricao.get_situacao_matricula_outra_chamada")
    @patch(
        "processoseletivo.models.Etapa.analise_documentacao_gerenciada",
        new_callable=PropertyMock,
    )
    def test_deveria_retornar_situacao_nao_compareceu(
        self, analise_documentacao, situacao_matricula
    ):
        analise_documentacao.return_value = True
        situacao_matricula.return_value = None
        etapa = recipes.etapa.make(encerrada=True)
        inscricao = recipes.inscricao.make(edicao=etapa.edicao)
        recipes.confirmacao.make(etapa=etapa, inscricao=inscricao)
        self.assertEqual(
            inscricao.get_situacao_matricula_em_chamada(etapa), "Não compareceu"
        )

    @patch("processoseletivo.models.Inscricao.get_situacao_matricula_outra_chamada")
    @patch("processoseletivo.models.Inscricao.get_situacao")
    @patch("processoseletivo.models.Inscricao.get_inscricao_outra_chamada")
    @patch(
        "processoseletivo.models.Etapa.analise_documentacao_gerenciada",
        new_callable=PropertyMock,
    )
    def test_deveria_retornar_situacao_lista_de_espera_com_inscricao_em_outra_chamada(
        self,
        analise_documentacao,
        inscricao_chamada,
        situacao_inscricao,
        situacao_matricula,
    ):
        analise_documentacao.return_value = False
        situacao_inscricao.return_value.get_mensagem.return_value = "Apto(a)"
        situacao_matricula.return_value = None
        etapa = recipes.etapa.make(encerrada=True)
        inscricao = recipes.inscricao.make(edicao=etapa.edicao)
        outra_inscricao = recipes.inscricao.make(edicao=etapa.edicao)
        inscricao_chamada.return_value = outra_inscricao
        self.assertEqual(
            inscricao.get_situacao_matricula_em_chamada(etapa), "Lista de Espera"
        )


@freeze_time("2020-08-20")
class ConfirmacaoInteresseCleanTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.etapa = recipes.etapa.make()

    def test_deveria_bloquear_confirmacao_de_etapa_ja_encerrada(self):
        etapa = recipes.etapa.make(encerrada=True)
        confirmacao = models.ConfirmacaoInteresse(etapa=etapa)
        with self.assertRaises(ValidationError) as ex:
            confirmacao.clean()

        self.assertIn("Etapa encerrada.", ex.exception.messages)

    def test_deveria_bloquear_confirmacao_com_analise_vigente(self):
        mommy.make(
            "editais.PeriodoConvocacao",
            evento=EventoCronogramaChoices.ANALISE.name,
            etapa=self.etapa,
            inicio=date(year=2020, month=3, day=19),
            fim=date(year=2020, month=3, day=21),
        )
        confirmacao = models.ConfirmacaoInteresse(etapa=self.etapa)
        with self.assertRaises(ValidationError) as ex:
            confirmacao.clean()

        self.assertIn(
            "A confirmação de interesse do candidato deve ser feita durante o período "
            "de Análise de Documentação.",
            ex.exception.messages,
        )

    def test_deveria_bloquear_mais_de_uma_confirmacao_do_mesmo_candidato(self):
        inscricao_a = recipes.inscricao.make()
        inscricao_b = recipes.inscricao.make(
            chamada=inscricao_a.chamada,
            edicao=inscricao_a.edicao,
            candidato=inscricao_a.candidato,
        )
        recipes.confirmacao.make(inscricao=inscricao_a, etapa=inscricao_a.chamada.etapa)
        confirmacao = models.ConfirmacaoInteresse(
            etapa=inscricao_b.chamada.etapa, inscricao=inscricao_b
        )
        with self.assertRaises(ValidationError) as ex:
            confirmacao.clean()

        self.assertIn(
            "Interesse do candidato já registrado nesta etapa em outra modalidade.",
            ex.exception.messages,
        )

    @patch("base.models.PessoaFisica.is_atualizado_recentemente")
    def test_deveria_bloquear_confirmacao_de_candidato_com_informacoes_nao_atualizadas(
        self, method
    ):
        method.return_value = False
        inscricao = recipes.inscricao.make()
        confirmacao = models.ConfirmacaoInteresse(
            etapa=inscricao.chamada.etapa, inscricao=inscricao
        )
        mommy.make(
            "editais.PeriodoConvocacao",
            evento=EventoCronogramaChoices.INTERESSE.name,
            etapa=inscricao.chamada.etapa,
            gerenciavel=True,
        )
        with self.assertRaises(ValidationError) as ex:
            confirmacao.clean()

        self.assertIn(
            "Os dados do candidato estão desatualizados.",
            ex.exception.messages,
        )

    @patch("base.models.PessoaFisica.is_atualizado_recentemente")
    @patch("base.models.PessoaFisica.has_dados_suap_completos")
    def test_deveria_bloquear_confirmacao_de_candidato_sem_dados_completos(
        self, has_dados, is_atualizado
    ):
        has_dados.return_value = False
        inscricao = recipes.inscricao.make()
        confirmacao = models.ConfirmacaoInteresse(
            etapa=inscricao.chamada.etapa, inscricao=inscricao
        )
        mommy.make(
            "editais.PeriodoConvocacao",
            evento=EventoCronogramaChoices.INTERESSE.name,
            etapa=inscricao.chamada.etapa,
            gerenciavel=True,
        )
        with self.assertRaises(ValidationError) as ex:
            confirmacao.clean()

        self.assertIn(
            "Candidato não preencheu os dados necessários para a pré-matrícula.",
            ex.exception.messages,
        )

    @patch("base.models.PessoaFisica.is_atualizado_recentemente")
    @patch("base.models.PessoaFisica.has_dados_suap_completos")
    def test_deveria_bloquear_confirmacao_de_candidato_sem_caracterizacao(
        self, has_dados, is_atualizado
    ):
        has_dados.return_value = True
        inscricao = recipes.inscricao.make()
        confirmacao = models.ConfirmacaoInteresse(
            etapa=inscricao.chamada.etapa, inscricao=inscricao
        )
        mommy.make(
            "editais.PeriodoConvocacao",
            evento=EventoCronogramaChoices.INTERESSE.name,
            etapa=inscricao.chamada.etapa,
            gerenciavel=True,
        )
        with self.assertRaises(ValidationError) as ex:
            confirmacao.clean()

        self.assertIn(
            "Os dados socioeconônicos do candidato não foram preenchidos.",
            ex.exception.messages,
        )

    @patch("base.models.PessoaFisica.is_atualizado_recentemente")
    @patch("base.models.PessoaFisica.has_dados_suap_completos")
    @patch("candidatos.models.Caracterizacao.is_atualizado_recentemente")
    def test_deveria_bloquear_confirmacao_de_candidato_com(
        self, caracterizacao_is_atualizada, has_dados, pessoa_is_atualizada
    ):
        caracterizacao_is_atualizada.return_value = False
        has_dados.return_value = True
        pessoa_is_atualizada.return_value = True
        inscricao = recipes.inscricao.make()
        confirmacao = models.ConfirmacaoInteresse(
            etapa=inscricao.chamada.etapa, inscricao=inscricao
        )
        mommy.make(
            "editais.PeriodoConvocacao",
            evento=EventoCronogramaChoices.INTERESSE.name,
            etapa=inscricao.chamada.etapa,
            gerenciavel=True,
        )
        raca = mommy.make("candidatos.Raca", descricao="parda")
        estado_civil = mommy.make("candidatos.EstadoCivil", descricao="casado")
        mommy.make(
            "candidatos.Caracterizacao",
            candidato=inscricao.candidato.pessoa,
            raca=raca,
            estado_civil=estado_civil,
            estado_civil_pai=estado_civil,
            estado_civil_mae=estado_civil,
        )
        with self.assertRaises(ValidationError) as ex:
            confirmacao.clean()

        self.assertIn(
            "Os dados socioeconônicos do candidato estão desatualizados.",
            ex.exception.messages,
        )

    @patch("base.models.PessoaFisica.is_atualizado_recentemente")
    def test_deveria_ser_valida_confirmacao_de_candidato_com_informacoes_atualizadas(
        self, method
    ):
        method.return_value = True
        inscricao = recipes.inscricao.make()
        confirmacao = models.ConfirmacaoInteresse(
            etapa=inscricao.chamada.etapa, inscricao=inscricao
        )
        self.assertIsNone(confirmacao.clean())


@freeze_time("2020-08-20")
class ConfirmacaoInteresseTestCase(DiretorEnsinoPermissionData, TestCase):
    def test_deveria_apagar_confirmacao_com_analise_vigente(self):
        confirmacao = recipes.confirmacao.make()
        mommy.make(
            "editais.PeriodoConvocacao",
            evento=EventoCronogramaChoices.ANALISE.name,
            etapa=confirmacao.etapa,
            inicio=date(year=2020, month=8, day=20),
            fim=date(year=2020, month=8, day=21),
        )
        self.assertTrue(confirmacao.pode_apagar())

    def test_nao_deveriar_apagar_confirmacao_com_analise_ja_realizada(self):
        confirmacao = recipes.confirmacao.make()
        mommy.make(
            "editais.PeriodoConvocacao",
            evento=EventoCronogramaChoices.ANALISE.name,
            etapa=confirmacao.etapa,
            inicio=date(year=2020, month=8, day=18),
            fim=date(year=2020, month=8, day=19),
        )
        self.assertFalse(confirmacao.pode_apagar())


class VagaTestCase(DiretorEnsinoPermissionData, TestCase):
    fixtures = ["modalidade.json"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.cota = models.Modalidade.objects.get(id=models.ModalidadeEnum.cota_racial)
        cls.ampla = models.Modalidade.objects.get(
            id=models.ModalidadeEnum.ampla_concorrencia
        )

    def test_vaga_deveriar_mudar_de_modalidade(self):
        vaga = recipes.vaga.make(modalidade=self.ampla)
        vaga._nova_transicao(self.cota)
        vaga_atualizada = models.Vaga.objects.get(id=vaga.id)
        self.assertEqual(vaga_atualizada.modalidade, self.cota)


class CicloArestasTestCase(TestCase):
    def test_nao_deveria_existir_ciclo_com_arestas_vazias(self):
        self.assertFalse(models.existe_ciclo([]))

    def test_deveria_existir_ciclo_com_apenas_uma_aresta_e_valores_iguais(self):
        self.assertTrue(models.existe_ciclo([("A", "A")]))

    def test_nao_deveria_existir_ciclo_com_pares_de_arestas_iguais(self):
        arestas = [("A", "B"), ("A", "B")]
        self.assertTrue(models.existe_ciclo(arestas))

    def test_deveria_existir_ciclo_com_duas_arestas_e_valores_invertidos(self):
        arestas = [("A", "B"), ("B", "A")]
        self.assertTrue(models.existe_ciclo(arestas))

    def test_nao_deveria_existir_ciclo_com_arestas_com_valores_diferentes(self):
        arestas = [("A", "B"), ("C", "D")]
        self.assertFalse(models.existe_ciclo(arestas))
