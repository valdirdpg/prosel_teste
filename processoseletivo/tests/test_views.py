import datetime
from unittest import mock

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse
from model_mommy import mommy

import base.tests.recipes
from base.models import PessoaFisica
from base.tests.mixins import UserTestMixin
from cursos.models import Campus, CursoSelecao
from cursos.tests.mixins import DiretorEnsinoPermissionData
from editais.choices import EventoCronogramaChoices
from editais.models import PeriodoConvocacao
from processoseletivo import models
from processoseletivo.models import Etapa
from psct.tests.utils import create
from . import recipes
from .. import views


class PSTestCase(TestCase):
    fixtures = [
        "psct/tests/fixtures/processo_seletivo.json",
        "psct/tests/fixtures/cursos.json",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("sync_permissions")
        cls.campus_jp = Campus.objects.get(pk=1)
        cls.processo_seletivo = models.ProcessoSeletivo.objects.first()
        cls.edicao = models.Edicao.objects.get(pk=1)
        cls.etapa_resultado = models.Etapa.objects.get(pk=1)
        cls.etapa = models.Etapa.objects.get(pk=2)
        cls.modalidade_ampla = models.Modalidade.objects.get(
            pk=models.ModalidadeEnum.ampla_concorrencia
        )
        cls.modalidade_cota_racial = models.Modalidade.objects.get(
            pk=models.ModalidadeEnum.cota_racial
        )
        cls.modalidade_renda_inferior_pcd = models.Modalidade.objects.get(
            pk=models.ModalidadeEnum.renda_inferior_pcd
        )
        cls.curso_fisica_subsequente_noturno = CursoSelecao.objects.get(pk=1)
        cls.pessoa = mommy.make(
            PessoaFisica,
            nome="John Doe",
            user__username="user",
            user__is_staff=True,
            user__is_active=True,
        )
        cls.pessoa.user.set_password("123")
        cls.pessoa.user.save()


class EtapaTestCase(PSTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.chamada = create(
            models.Chamada,
            etapa=cls.etapa,
            modalidade=cls.modalidade_ampla,
            multiplicador=3,
            vagas=3,
            curso=cls.curso_fisica_subsequente_noturno,
        )
        cls.candidato = mommy.make(models.Candidato, pessoa=cls.pessoa)
        cls.inscricao_cotista = mommy.make(
            models.Inscricao,
            candidato=cls.candidato,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_cota_racial,
            edicao=cls.edicao,
            chamada=cls.chamada,
        )
        cls.interesse_cotista = mommy.make(
            models.ConfirmacaoInteresse,
            inscricao=cls.inscricao_cotista,
            etapa=cls.etapa,
        )
        cls.analise = mommy.make(
            models.AnaliseDocumental, confirmacao_interesse=cls.interesse_cotista
        )
        cls.tipo_analise_eep_cotista = mommy.make(
            models.TipoAnalise, nome="AVALIAÇÃO EGRESSO DE ESCOLA PÚBLICA"
        )
        cls.tipo_analise_medica_cotista = mommy.make(
            models.TipoAnalise, nome="AVALIAÇÃO MÉDICA"
        )
        cls.inscricao_cotista.modalidade.tipos_analise.add(cls.tipo_analise_eep_cotista)
        cls.avaliacao_cotista = mommy.make(
            models.AvaliacaoDocumental,
            analise_documental=cls.analise,
            tipo_analise=cls.tipo_analise_eep_cotista,
        )
        cls.avaliacao2_cotista = mommy.make(
            models.AvaliacaoDocumental,
            analise_documental=cls.analise,
            tipo_analise=cls.tipo_analise_medica_cotista,
        )

    def test_etapa_nao_publicada(self):
        self.etapa_resultado.publica = False
        self.etapa_resultado.save()
        url = reverse(
            "edicao_etapa",
            kwargs={"edicao_pk": self.edicao.pk, "etapa_pk": self.etapa_resultado.pk},
        )
        r = self.client.get(url, follow=True)
        self.assertContains(r, "Não há vagas cadastradas para a")
        self.assertContains(
            r, "processo seletivo. Para mais informações, entre em contato com a"
        )

    def test_etapa_publicada_sem_vagas(self):
        self.etapa_resultado.publica = True
        self.etapa_resultado.save()
        url = reverse(
            "edicao_etapa",
            kwargs={"edicao_pk": self.edicao.pk, "etapa_pk": self.etapa_resultado.pk},
        )
        r = self.client.get(url, follow=True)
        msg = f"Não há vagas cadastradas"
        self.assertContains(r, msg)

    def test_etapa_publicada_com_vagas(self):
        self.etapa_resultado.publica = True
        self.etapa_resultado.save()
        chamada = create(
            models.Chamada,
            etapa=self.etapa_resultado,
            modalidade=self.modalidade_ampla,
            multiplicador=3,
            vagas=3,
            curso=self.curso_fisica_subsequente_noturno,
        )
        url = reverse(
            "edicao_etapa",
            kwargs={"edicao_pk": self.edicao.pk, "etapa_pk": self.etapa_resultado.pk},
        )
        r = self.client.get(url, follow=True)
        msg = f"Não há vagas cadastradas"
        self.assertNotContains(r, msg)
        url_cursos_no_campus = reverse(
            "cursos",
            kwargs={"pk": self.etapa_resultado.pk, "campus": chamada.curso.campus.pk},
        )
        self.assertContains(r, url_cursos_no_campus)
        self.assertContains(r, f"{chamada.vagas}</td>")

    def test_matricula_retardatarios(self):
        self.admin_group = Group.objects.get(
            name="Administradores Sistêmicos de Chamadas"
        )
        self.pessoa.user.groups.add(self.admin_group)
        self.pessoa.user.save()
        self.client.login(username=self.pessoa.user.username, password="123")
        self.edicao.importado = True
        self.edicao.save()

        self.data = {
            "edicao": self.edicao.pk,
            "campus": self.campus_jp.pk,
            "multiplicador": 1,
            "cronogramas_convocacao-0-nome": "Manifestação de Interesse",
            "cronogramas_convocacao-0-inicio": "15/01/2019",
            "cronogramas_convocacao-0-fim": "15/01/2019",
            "cronogramas_convocacao-0-evento": EventoCronogramaChoices.INTERESSE.name,
            "cronogramas_convocacao-1-nome": "Análise de documentação",
            "cronogramas_convocacao-1-inicio": "15/01/2019",
            "cronogramas_convocacao-1-fim": "15/01/2019",
            "cronogramas_convocacao-1-evento": EventoCronogramaChoices.ANALISE.name,
            "cronogramas_convocacao-2-nome": "Confirmação de matrícula",
            "cronogramas_convocacao-2-inicio": "15/01/2019",
            "cronogramas_convocacao-2-fim": "15/01/2019",
            "cronogramas_convocacao-2-evento": EventoCronogramaChoices.CONFIRMACAO.name,
            "cronogramas_convocacao-3-nome": "Manifestação de Interesse",
            "cronogramas_convocacao-3-inicio": "15/01/2019",
            "cronogramas_convocacao-3-fim": "15/01/2019",
            "cronogramas_convocacao-3-evento": EventoCronogramaChoices.INTERESSE.name,
            "cronogramas_convocacao-TOTAL_FORMS": 4,
            "cronogramas_convocacao-INITIAL_FORMS": 0,
            "cronogramas_convocacao-MIN_NUM_FORMS": 0,
            "cronogramas_convocacao-MAX_NUM_FORMS": 1000,
        }

        url = reverse("admin:processoseletivo_etapa_add")
        response = self.client.post(url, self.data, follow=True)
        self.assertContains(response, "foi adicionado com sucesso")

    def test_encerrar_etapa_qtd_avaliacao_incorreta(self):
        msg = (
            f"A inscricão do candidato {self.inscricao_cotista.candidato} possui "
            f"quantidade de avaliações diferente dos tipos de análise da modalidade"
        )
        self.inscricao_cotista.chamada.etapa.reabrir()
        with self.assertRaises(Etapa.EncerrarEtapaError) as cm:
            self.inscricao_cotista.chamada.etapa.encerrar()
        exception = cm.exception
        self.assertIn(msg, exception.messages)

    def test_encerrar_etapa_avaliacao_inexistente(self):
        msg = (
            f"A inscrição do candidato {self.inscricao_cotista.candidato} possui "
            f"avaliação inexistente nos tipos de análise da cota"
        )
        self.inscricao_cotista.chamada.etapa.reabrir()
        with self.assertRaises(Etapa.EncerrarEtapaError) as cm:
            self.inscricao_cotista.chamada.etapa.encerrar()
        exception = cm.exception
        self.assertIn(msg, exception.messages)

    def test_encerrar_etapa_duas_excecoes_ao_mesmo_tempo(self):
        self.inscricao_cotista.chamada.etapa.reabrir()
        with self.assertRaises(Etapa.EncerrarEtapaError) as cm:
            self.inscricao_cotista.chamada.etapa.encerrar()
        exception = cm.exception
        self.assertEqual(2, len(list(exception)))

    def test_visualizar_mensagem_excecao_etapa(self):
        self.admin_group = Group.objects.get(
            name="Administradores Sistêmicos de Chamadas"
        )
        self.pessoa.user.groups.add(self.admin_group)
        self.pessoa.user.save()

        self.client.login(username=self.pessoa.user.username, password="123")

        self.data = {
            "edicao": self.edicao.pk,
            "campus": self.campus_jp.pk,
            "multiplicador": 1,
            "cronogramas_convocacao-0-nome": "Manifestação de Interesse",
            "cronogramas_convocacao-0-inicio": "27/03/2019",
            "cronogramas_convocacao-0-fim": "27/03/2019",
            "cronogramas_convocacao-0-evento": EventoCronogramaChoices.INTERESSE.name,
            "cronogramas_convocacao-1-nome": "Análise de documentação",
            "cronogramas_convocacao-1-inicio": "27/03/2019",
            "cronogramas_convocacao-1-fim": "27/03/2019",
            "cronogramas_convocacao-1-evento": EventoCronogramaChoices.ANALISE.name,
            "cronogramas_convocacao-2-nome": "Confirmação de matrícula",
            "cronogramas_convocacao-2-inicio": "27/03/2019",
            "cronogramas_convocacao-2-fim": "27/03/2019",
            "cronogramas_convocacao-2-evento": EventoCronogramaChoices.CONFIRMACAO.name,
            "cronogramas_convocacao-3-nome": "Manifestação de Interesse",
            "cronogramas_convocacao-3-inicio": "27/03/2019",
            "cronogramas_convocacao-3-fim": "27/03/2019",
            "cronogramas_convocacao-3-evento": EventoCronogramaChoices.INTERESSE.name,
            "cronogramas_convocacao-4-nome": "Manifestação de Interesse",
            "cronogramas_convocacao-4-inicio": "27/03/2019",
            "cronogramas_convocacao-4-fim": "27/03/2019",
            "cronogramas_convocacao-4-evento": EventoCronogramaChoices.INTERESSE.name,
            "cronogramas_convocacao-TOTAL_FORMS": 5,
            "cronogramas_convocacao-INITIAL_FORMS": 0,
            "cronogramas_convocacao-MIN_NUM_FORMS": 0,
            "cronogramas_convocacao-MAX_NUM_FORMS": 1000,
        }
        url = reverse("admin:processoseletivo_etapa_add")
        response = self.client.post(url, self.data, follow=True)
        self.assertContains(
            response,
            "No Cronograma devem existir, no máximo, 2 (DOIS) eventos de Interesse de Matrícula.",
        )


class EdicaoTestCase(PSTestCase):
    def test_visualizar_edicao(self):
        edicao = mommy.make(models.Edicao, processo_seletivo=self.processo_seletivo)
        url = reverse("processoseletivo", args=[self.processo_seletivo.pk])
        r = self.client.get(url, follow=True)
        self.assertContains(r, edicao)


class LoginAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.pessoa = mommy.make(
            PessoaFisica,
            nome="John Doe",
            user__username="user",
            user__is_staff=True,
            user__is_active=True,
        )
        cls.pessoa.user.set_password("123")
        cls.pessoa.user.save()

    def test_acesso_pagina_login_admin(self):
        r = self.client.get("/admin/login/")
        self.assertContains(r, "Acesso para Administradores")

    def test_realiza_login_admin(self):
        r = self.client.login(username="user", password="123")
        self.assertTrue(r)
        r = self.client.get("/admin", follow=True)
        self.assertContains(r, "Administração do Site")


class CandidatoCotaParaAmplaTestCase(PSTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.grupo_administradores_chamadas = Group.objects.get(name=models.GRUPO_CAMPI)
        cls.pessoa.user.groups.add(cls.grupo_administradores_chamadas)
        cls.pessoa.user.save()
        cls.etapa.encerrada = False
        cls.periodo_confirmacao = create(
            PeriodoConvocacao,
            inicio=(datetime.datetime.now() - datetime.timedelta(days=1)).date(),
            fim=(datetime.datetime.now() - datetime.timedelta(days=1)).date(),
            evento=EventoCronogramaChoices.ANALISE.name,
            etapa=cls.etapa,
            gerenciavel=True,
        )
        cls.chamada = create(
            models.Chamada,
            etapa=cls.etapa,
            modalidade=cls.modalidade_ampla,
            multiplicador=1,
            vagas=2,
            curso=cls.curso_fisica_subsequente_noturno,
        )
        cls.candidato = mommy.make(models.Candidato, pessoa=cls.pessoa)
        cls.inscricao = mommy.make(
            models.Inscricao,
            candidato=cls.candidato,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_ampla,
            edicao=cls.edicao,
            chamada=cls.chamada,
        )
        cls.interesse = mommy.make(
            models.ConfirmacaoInteresse, inscricao=cls.inscricao, etapa=cls.etapa
        )
        cls.analise = mommy.make(
            models.AnaliseDocumental,
            confirmacao_interesse=cls.interesse,
            situacao_final=True,
        )

        cls.chamada_cota = create(
            models.Chamada,
            etapa=cls.etapa,
            modalidade=cls.modalidade_cota_racial,
            multiplicador=2,
            vagas=1,
            curso=cls.curso_fisica_subsequente_noturno,
        )
        create(
            models.Vaga,
            edicao=cls.edicao,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_cota_racial,
            modalidade_primaria=cls.modalidade_cota_racial,
        )
        create(
            models.Vaga,
            edicao=cls.edicao,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_ampla,
            modalidade_primaria=cls.modalidade_ampla,
        )
        create(
            models.Vaga,
            edicao=cls.edicao,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_ampla,
            modalidade_primaria=cls.modalidade_ampla,
        )

        # dados do candidato que vai pegar a vaga da cota

        cls.pessoa_2 = mommy.make(
            PessoaFisica,
            nome="Joe Caruso",
            user__username="user2",
            user__is_staff=True,
            user__is_active=True,
        )
        cls.candidato_2 = mommy.make(models.Candidato, pessoa=cls.pessoa_2)
        cls.inscricao_cota_2 = mommy.make(
            models.Inscricao,
            candidato=cls.candidato_2,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_cota_racial,
            edicao=cls.edicao,
            chamada=cls.chamada_cota,
        )
        cls.interesse_cota_2 = mommy.make(
            models.ConfirmacaoInteresse, inscricao=cls.inscricao_cota_2, etapa=cls.etapa
        )
        cls.analise_cota_2 = mommy.make(
            models.AnaliseDocumental,
            confirmacao_interesse=cls.interesse_cota_2,
            situacao_final=True,
        )

        # dados do candidato que será movido para a ampla

        cls.pessoa_3 = mommy.make(
            PessoaFisica,
            nome="Chris Rock",
            user__username="user3",
            user__is_staff=True,
            user__is_active=True,
        )
        cls.candidato_3 = mommy.make(models.Candidato, pessoa=cls.pessoa_3)
        cls.inscricao_cota_1 = mommy.make(
            models.Inscricao,
            candidato=cls.candidato_3,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_cota_racial,
            edicao=cls.edicao,
            chamada=cls.chamada_cota,
        )
        cls.inscricao_ampla_1 = mommy.make(
            models.Inscricao,
            candidato=cls.candidato_3,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_ampla,
            edicao=cls.edicao,
            chamada=cls.chamada,
        )
        cls.interesse_cota = mommy.make(
            models.ConfirmacaoInteresse, inscricao=cls.inscricao_cota_1, etapa=cls.etapa
        )
        cls.analise_cota = mommy.make(
            models.AnaliseDocumental,
            confirmacao_interesse=cls.interesse_cota,
            situacao_final=True,
        )

        cls.etapa.encerrar()

    def test_confirmacao_na_ampla(self):
        confirmacao_na_ampla = models.ConfirmacaoInteresse.objects.filter(
            inscricao=self.inscricao_ampla_1, etapa=self.etapa
        ).exists()
        self.assertTrue(confirmacao_na_ampla)

    def test_confirmacao_na_cota(self):
        confirmacao_na_cota = models.ConfirmacaoInteresse.objects.filter(
            inscricao=self.inscricao_cota_1, etapa=self.etapa
        ).exists()
        self.assertFalse(confirmacao_na_cota)

    def test_matriculado_na_ampla(self):
        matriculado_na_ampla = models.Matricula.objects.filter(
            inscricao=self.inscricao_ampla_1, etapa=self.etapa
        ).exists()
        self.assertTrue(matriculado_na_ampla)

    def test_matriculado_na_cota(self):
        matriculado_na_cota = models.Matricula.objects.filter(
            inscricao=self.inscricao_cota_1, etapa=self.etapa
        ).exists()
        self.assertFalse(matriculado_na_cota)


class ChamadaTestCase(PSTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.grupo_administradores_chamadas = Group.objects.get(name=models.GRUPO_CAMPI)
        cls.pessoa.user.groups.add(cls.grupo_administradores_chamadas)
        cls.pessoa.user.save()
        cls.etapa.encerrada = False
        cls.chamada = create(
            models.Chamada,
            etapa=cls.etapa,
            modalidade=cls.modalidade_ampla,
            multiplicador=3,
            vagas=3,
            curso=cls.curso_fisica_subsequente_noturno,
        )
        cls.candidato = mommy.make(models.Candidato, pessoa=cls.pessoa)
        cls.inscricao = mommy.make(
            models.Inscricao,
            candidato=cls.candidato,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_ampla,
            edicao=cls.edicao,
            chamada=cls.chamada,
        )
        cls.interesse = mommy.make(
            models.ConfirmacaoInteresse, inscricao=cls.inscricao, etapa=cls.etapa
        )
        cls.analise = mommy.make(
            models.AnaliseDocumental, confirmacao_interesse=cls.interesse
        )

    def test_pagina_de_chamadas(self):
        self.client.login(username="user", password="123")
        url = reverse("admin:processoseletivo_chamada_changelist")
        r = self.client.get(url, follow=True)
        self.assertContains(r, "Selecione chamada para modificar")

    def test_pode_ver_lista_chamadas(self):
        self.client.login(username="user", password="123")
        url = reverse("admin:processoseletivo_chamada_changelist")
        r = self.client.get(url, follow=True)
        # O usuário logado não tem associação com nenhum campus, por isso não deve ver as chamadas.
        self.assertFalse(self.pessoa.user.lotacoes.exists())
        self.assertNotContains(
            r, reverse("admin:processoseletivo_chamada_change", args=[self.chamada.pk])
        )

        # O usuário passa a ser servidor do campus e pode ver e alterar a chamada.
        self.pessoa.user.lotacoes.add(self.campus_jp)
        self.assertTrue(self.pessoa.user.lotacoes.exists())
        r = self.client.get(url, follow=True)
        self.assertContains(
            r, reverse("admin:processoseletivo_chamada_change", args=[self.chamada.pk])
        )

    def test_pode_ver_inscritos(self):
        self.pessoa.user.lotacoes.add(self.campus_jp)
        self.client.login(username="user", password="123")
        url = reverse("admin:processoseletivo_chamada_change", args=[self.chamada.pk])
        r = self.client.get(url, follow=True)
        self.assertContains(r, "Modificar chamada")
        self.assertContains(r, self.inscricao.candidato.pessoa.nome.upper())

    def test_pode_deletar(self):
        # apenas o super usuário pode
        self.pessoa.user.lotacoes.add(self.campus_jp)
        self.pessoa.user.is_superuser = True
        self.pessoa.user.save()
        self.client.login(username="user", password="123")
        url = reverse("admin:processoseletivo_chamada_change", args=[self.chamada.pk])
        r = self.client.get(url, follow=True)
        self.assertContains(r, "Modificar chamada")
        self.assertContains(r, 'class="deletelink-box"')

    def test_nao_pode_deletar(self):
        self.pessoa.user.lotacoes.add(self.campus_jp)
        self.pessoa.user.is_superuser = False
        self.pessoa.user.save()
        self.client.login(username="user", password="123")
        url = reverse("admin:processoseletivo_chamada_change", args=[self.chamada.pk])
        r = self.client.get(url, follow=True)
        self.assertContains(r, "Modificar chamada")
        self.assertNotContains(r, 'class="deletelink-box"')

    def test_confirma_delecao_chamada(self):
        self.pessoa.user.lotacoes.add(self.campus_jp)
        self.pessoa.user.is_superuser = True
        self.pessoa.user.save()
        self.client.login(username="user", password="123")
        url = reverse("admin:processoseletivo_chamada_delete", args=[self.chamada.pk])
        r = self.client.get(url, follow=True)
        self.assertContains(r, "Tem certeza?")
        self.assertContains(r, "Confirmações de Interesse: 1")
        self.assertContains(r, "Confirmações de Interesse dos seguintes candidatos:")
        self.assertContains(r, "Análises de Documentos: 1")
        self.assertContains(r, "Análises de Documentos dos seguintes candidatos:")
        self.assertContains(r, self.pessoa.nome.upper())

    def test_deleta_chamada_e_dependentes(self):
        self.pessoa.user.lotacoes.add(self.campus_jp)
        self.pessoa.user.is_superuser = True
        self.pessoa.user.save()
        self.client.login(username="user", password="123")
        # Verifica a existência das dependências a serem deletadas
        self.assertTrue(self.chamada.get_confirmacoes_interesse().exists())
        self.assertTrue(self.chamada.get_analises_documentais().exists())
        url = reverse("admin:processoseletivo_chamada_delete", args=[self.chamada.pk])
        # Executa a deleção da chamada
        r = self.client.post(url, data={"post": "yes"}, follow=True)
        # Verifica a exclusão
        self.assertContains(r, "excluído com sucesso")
        self.assertFalse(self.chamada.get_confirmacoes_interesse().exists())
        self.assertFalse(self.chamada.get_analises_documentais().exists())
        self.assertFalse(models.Chamada.objects.filter(pk=self.chamada.pk).exists())

    def test_ver_vagas_de_um_curso_uma_chamada(self):
        self.etapa_resultado.publica = True
        self.etapa_resultado.save()
        chamada = create(
            models.Chamada,
            etapa=self.etapa_resultado,
            modalidade=self.modalidade_ampla,
            multiplicador=3,
            vagas=3,
            curso=self.curso_fisica_subsequente_noturno,
        )
        campus = chamada.curso.campus
        curso = self.curso_fisica_subsequente_noturno
        url = reverse(
            "cursos", kwargs={"pk": self.etapa_resultado.pk, "campus": campus.pk}
        )
        r = self.client.get(url, follow=True)
        self.assertContains(r, curso.nome)

    def test_ver_candidatos_chamados(self):
        self.etapa_resultado.publica = True
        self.etapa_resultado.save()
        chamada = create(
            models.Chamada,
            etapa=self.etapa_resultado,
            modalidade=self.modalidade_ampla,
            multiplicador=3,
            vagas=3,
            curso=self.curso_fisica_subsequente_noturno,
        )
        campus = chamada.curso.campus
        curso = self.curso_fisica_subsequente_noturno
        url = reverse(
            "chamadas",
            kwargs={
                "pk": self.etapa_resultado.pk,
                "campus": campus.pk,
                "curso": curso.pk,
            },
        )
        r = self.client.get(url, follow=True)
        self.assertContains(r, "Candidatos convocados")
        self.assertContains(r, f"{chamada.vagas} vaga(s)")
        # testar se aparecem o nomes do candidatos convocados.


class ChamadaConvocadoOutraCotaTestCase(PSTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.grupo_administradores_chamadas = Group.objects.get(name=models.GRUPO_CAMPI)
        cls.pessoa.user.groups.add(cls.grupo_administradores_chamadas)
        cls.pessoa.user.save()
        cls.etapa.encerrada = False

        cls.candidato_1 = mommy.make(models.Candidato)
        # deve aparecer como 'Matriculado(a) em cota' na lista da ampla

        cls.candidato_2 = mommy.make(models.Candidato)
        # deve pegar a vaga da ampla

        cls.candidato_3 = mommy.make(models.Candidato)
        # deve aparecer como 'Lista de Espera' nas duas chamadas

        # chamadas
        cls.chamada_ampla = mommy.make(
            models.Chamada,
            etapa=cls.etapa,
            modalidade=cls.modalidade_ampla,
            curso=cls.curso_fisica_subsequente_noturno,
            multiplicador=2,
            vagas=1,
        )
        cls.chamada_cota = mommy.make(
            models.Chamada,
            etapa=cls.etapa,
            modalidade=cls.modalidade_cota_racial,
            curso=cls.curso_fisica_subsequente_noturno,
            multiplicador=3,
            vagas=1,
        )

        # vagas
        create(
            models.Vaga,
            edicao=cls.edicao,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_ampla,
            modalidade_primaria=cls.modalidade_ampla,
        )
        create(
            models.Vaga,
            edicao=cls.edicao,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_cota_racial,
            modalidade_primaria=cls.modalidade_cota_racial,
        )

        # inscricoes
        cls.inscricao_ampla_1 = mommy.make(
            models.Inscricao,
            candidato=cls.candidato_1,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_ampla,
            edicao=cls.edicao,
            chamada=cls.chamada_ampla,
        )
        cls.inscricao_cota_1 = mommy.make(
            models.Inscricao,
            candidato=cls.candidato_1,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_cota_racial,
            edicao=cls.edicao,
            chamada=cls.chamada_cota,
        )

        cls.inscricao_ampla_2 = mommy.make(
            models.Inscricao,
            candidato=cls.candidato_2,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_ampla,
            edicao=cls.edicao,
            chamada=cls.chamada_ampla,
        )
        cls.inscricao_ampla_3 = mommy.make(
            models.Inscricao,
            candidato=cls.candidato_3,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_ampla,
            edicao=cls.edicao,
            chamada=cls.chamada_ampla,
        )
        cls.inscricao_cota_3 = mommy.make(
            models.Inscricao,
            candidato=cls.candidato_3,
            curso=cls.curso_fisica_subsequente_noturno,
            modalidade=cls.modalidade_cota_racial,
            edicao=cls.edicao,
            chamada=cls.chamada_cota,
        )

        # interesses
        cls.interesse_cota_1 = mommy.make(
            models.ConfirmacaoInteresse, inscricao=cls.inscricao_cota_1, etapa=cls.etapa
        )
        cls.interesse_ampla_2 = mommy.make(
            models.ConfirmacaoInteresse,
            inscricao=cls.inscricao_ampla_2,
            etapa=cls.etapa,
        )
        cls.interesse_cota_3 = mommy.make(
            models.ConfirmacaoInteresse, inscricao=cls.inscricao_cota_3, etapa=cls.etapa
        )

        # desempenhos
        cls.desempenho_ins_cota_1 = mommy.make(
            models.Desempenho, inscricao=cls.inscricao_cota_1, nota_geral=90.0
        )
        cls.desempenho_ins_ampla_2 = mommy.make(
            models.Desempenho, inscricao=cls.inscricao_ampla_2, nota_geral=85.0
        )
        cls.desempenho_ins_cota_3 = mommy.make(
            models.Desempenho, inscricao=cls.inscricao_cota_3, nota_geral=80.0
        )

        hoje = datetime.date.today()
        cls.periodo_convocacao = mommy.make(
            PeriodoConvocacao,
            tipo="CONVOCACAO",
            evento="ANALISE",
            inscricao=False,
            gerenciavel=False,
            etapa=cls.etapa,
            inicio=hoje - datetime.timedelta(days=1),
            fim=hoje - datetime.timedelta(days=1),
        )

        # encerrar etapa
        cls.etapa.encerrar()

    def test_matriculado_em_cota(self):
        self.client.login(username="user", password="123")
        self.pessoa.user.lotacoes.add(self.campus_jp)
        url = reverse(
            "admin:processoseletivo_chamada_change", args=[self.chamada_ampla.pk]
        )
        r = self.client.get(url, follow=True)
        self.assertContains(r, self.candidato_1.pessoa.nome.upper())
        self.assertContains(r, "Matriculado(a) em Cota")

    def test_candidato_msg_lista_espera_em_duas_chamadas(self):
        self.client.login(username="user", password="123")
        self.pessoa.user.lotacoes.add(self.campus_jp)
        url = reverse(
            "chamadas",
            kwargs={
                "pk": self.etapa.pk,
                "campus": self.campus_jp.pk,
                "curso": self.curso_fisica_subsequente_noturno.pk,
            },
        )
        r = self.client.get(url, follow=True)
        self.assertContains(r, self.candidato_2.pessoa.nome.upper())
        self.assertContains(r, "<td>Lista de Espera</td>", count=2)
        self.assertNotContains(r, "Não compareceu")


class AnaliseDocumentalTestCase(ChamadaTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.candidato_cotista = mommy.make(models.Candidato)
        cls.chamada_cota_racial = create(
            models.Chamada,
            etapa=cls.etapa,
            modalidade=cls.modalidade_cota_racial,
            multiplicador=3,
            vagas=3,
            curso=cls.curso_fisica_subsequente_noturno,
        )

    def setUp(self):
        super().setUp()
        self.inscricao_cotista = mommy.make(
            models.Inscricao,
            candidato=self.candidato_cotista,
            curso=self.curso_fisica_subsequente_noturno,
            modalidade=self.modalidade_cota_racial,
            edicao=self.edicao,
            chamada=self.chamada_cota_racial,
        )
        self.interesse_cotista = mommy.make(
            models.ConfirmacaoInteresse,
            inscricao=self.inscricao_cotista,
            etapa=self.etapa,
        )
        self.analise_cotista = mommy.make(
            models.AnaliseDocumental,
            confirmacao_interesse=self.interesse_cotista,
            situacao_final=False,
        )

    def acesso_admin_campus(self):
        self.pessoa.user.lotacoes.add(self.campus_jp)
        self.pessoa.user.save()
        self.client.login(username="user", password="123")

    def adicionar_inscricao_ampla(self):
        self.inscricao_cotista_ampla = mommy.make(
            models.Inscricao,
            candidato=self.candidato_cotista,
            curso=self.curso_fisica_subsequente_noturno,
            modalidade=self.modalidade_ampla,
            edicao=self.edicao,
            chamada=self.chamada,
        )

    def adicionar_analise_ampla(self):
        self.assertFalse(
            models.Inscricao.objects.filter(
                candidato=self.candidato_cotista,
                modalidade__id=models.ModalidadeEnum.ampla_concorrencia,
            ).exists()
        )
        self.adicionar_inscricao_ampla()
        self.interesse_cotista_ampla = mommy.make(
            models.ConfirmacaoInteresse,
            inscricao=self.inscricao_cotista_ampla,
            etapa=self.etapa,
        )
        self.analise_cotista_ampla = mommy.make(
            models.AnaliseDocumental,
            confirmacao_interesse=self.interesse_cotista_ampla,
            situacao_final=True,
        )

    def pode_replicar(self, analise, status_assert=True):
        url = reverse(
            "admin:processoseletivo_analisedocumental_change", args=[analise.pk]
        )
        r = self.client.get(url, follow=True)
        if status_assert:
            self.assertContains(
                r, reverse("replicar_analise_documental", args=[analise.pk])
            )
        else:
            self.assertNotContains(
                r, reverse("replicar_analise_documental", args=[analise.pk])
            )

    def deferimento_analise(self, analise):
        analise.situacao_final = True
        analise.save()

    def indeferimento_analise(self, analise):
        analise.situacao_final = False
        analise.save()

    def test_pode_replicar_analise_cotista_sem_ampla(self):
        self.acesso_admin_campus()

        self.deferimento_analise(self.analise_cotista)
        self.pode_replicar(self.analise_cotista, False)

        self.indeferimento_analise(self.analise_cotista)
        self.pode_replicar(self.analise_cotista, False)

    def test_pode_replicar_analise_cotista_com_ampla(self):
        self.acesso_admin_campus()
        self.adicionar_inscricao_ampla()

        self.deferimento_analise(self.analise_cotista)
        self.pode_replicar(self.analise_cotista, False)

        self.indeferimento_analise(self.analise_cotista)
        self.pode_replicar(self.analise_cotista, True)

    def test_apagar_interesse(self):
        qtde_analises = models.AnaliseDocumental.objects.all().count()
        self.interesse_cotista.delete()
        self.assertEquals(
            models.AnaliseDocumental.objects.all().count(), qtde_analises - 1
        )

    def test_fluxo_principal_replicar_analise(self):
        self.adicionar_inscricao_ampla()
        self.acesso_admin_campus()

        self.assertFalse(
            models.AnaliseDocumental.objects.get(
                pk=self.analise_cotista.pk
            ).situacao_final
        )
        qtde_analises = models.AnaliseDocumental.objects.count()
        url = reverse("replicar_analise_documental", args=[self.analise_cotista.pk])
        r = self.client.post(url, follow=True)
        self.assertEquals(qtde_analises + 1, models.AnaliseDocumental.objects.count())
        self.assertContains(r, "lise Documental criada com sucesso")
        self.assertContains(r, "Ampla Concorrência")

    def test_fluxo_secundario_replicar_analise(self):
        self.adicionar_analise_ampla()
        self.acesso_admin_campus()

        self.assertFalse(
            models.AnaliseDocumental.objects.get(
                pk=self.analise_cotista.pk
            ).situacao_final
        )
        qtde_analises = models.AnaliseDocumental.objects.count()
        url = reverse("replicar_analise_documental", args=[self.analise_cotista.pk])
        r = self.client.post(url, follow=True)
        self.assertEquals(qtde_analises, models.AnaliseDocumental.objects.count())
        self.assertContains(r, "lise de documentos de ampla concorrência já existe")
        self.assertContains(r, url)

    def test_fluxo_secundario_replicar_analise_sem_ampla(self):
        self.acesso_admin_campus()

        self.assertFalse(
            models.AnaliseDocumental.objects.get(
                pk=self.analise_cotista.pk
            ).situacao_final
        )
        qtde_analises = models.AnaliseDocumental.objects.count()
        url = reverse("replicar_analise_documental", args=[self.analise_cotista.pk])
        r = self.client.post(url, follow=True)
        self.assertEquals(qtde_analises, models.AnaliseDocumental.objects.count())
        self.assertContains(
            r, "Não há convocação de ampla concorrência para este candidato."
        )
        self.assertNotContains(r, url)


class AvaliacaoMedicaTestCase(ChamadaTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.candidato_pcd = mommy.make(
            models.Candidato, pessoa__nome="José da Silva", pessoa__cpf="123.456.789.10"
        )
        cls.chamada_renda_inferior_pcd = create(
            models.Chamada,
            etapa=cls.etapa,
            modalidade=cls.modalidade_renda_inferior_pcd,
            multiplicador=3,
            vagas=3,
            curso=cls.curso_fisica_subsequente_noturno,
        )
        cls.tipo_analise_medica = mommy.make(
            models.TipoAnalise, nome="AVALIAÇÃO MÉDICA"
        )

    def setUp(self):
        super().setUp()
        mommy.make(
            PeriodoConvocacao,
            etapa=self.etapa,
            evento="ANALISE",
            gerenciavel=True,
            inicio=datetime.date.today(),
            fim=datetime.date.today(),
        )
        self.etapa.encerrada = False
        self.etapa.save()
        self.inscricao_pcd = mommy.make(
            models.Inscricao,
            candidato=self.candidato_pcd,
            curso=self.curso_fisica_subsequente_noturno,
            modalidade=self.modalidade_renda_inferior_pcd,
            edicao=self.edicao,
            chamada=self.chamada_renda_inferior_pcd,
        )
        self.interesse_pcd = mommy.make(
            models.ConfirmacaoInteresse, inscricao=self.inscricao_pcd, etapa=self.etapa
        )
        mommy.make(
            PeriodoConvocacao,
            etapa=self.etapa,
            evento=EventoCronogramaChoices.ANALISE.name,
            gerenciavel=True,
        )

    def acesso_admin_campus(self):
        self.pessoa.user.lotacoes.add(self.campus_jp)
        self.pessoa.user.save()
        self.client.login(username="user", password="123")

    def adicionar_analise(self):
        analise = models.AnaliseDocumental.objects.filter(
            confirmacao_interesse=self.interesse_pcd
        ).first()
        if analise:
            self.analise_pcd = analise
        else:
            self.analise_pcd = mommy.make(
                models.AnaliseDocumental, confirmacao_interesse=self.interesse_pcd
            )

    def adicionar_avaliacao_medica(self):
        self.adicionar_analise()
        self.avaliacao_medica = mommy.make(
            models.AvaliacaoDocumental,
            analise_documental=self.analise_pcd,
            tipo_analise=self.tipo_analise_medica,
        )

    def test_avaliacao_medica_nao_realizada(self):
        self.acesso_admin_campus()
        url = reverse("avaliacao_medica_changelist")
        r = self.client.get(f"{url}?tab=nao_avaliadas", follow=True)
        self.assertContains(r, "Avaliações de Documentação Médica")
        self.assertContains(r, self.candidato_pcd.pessoa)
        self.assertContains(
            r, reverse("avaliacao_medica_add", args=[self.inscricao_pcd.pk])
        )

        r = self.client.get(f"{url}?tab=avaliadas", follow=True)
        self.assertContains(r, "Avaliações de Documentação Médica")
        self.assertNotContains(r, self.candidato_pcd.pessoa)
        self.assertNotContains(
            r, reverse("avaliacao_medica_add", args=[self.inscricao_pcd.pk])
        )

    def test_analise_sem_avaliacao_medica_realizada(self):
        self.adicionar_analise()
        self.test_avaliacao_medica_nao_realizada()

    def test_avaliacao_medica_realizada(self):
        self.adicionar_avaliacao_medica()
        self.acesso_admin_campus()

        url = reverse("avaliacao_medica_changelist")
        r = self.client.get(f"{url}?tab=avaliadas", follow=True)
        self.assertContains(r, "Avaliações de Documentação Médica")
        self.assertContains(r, self.candidato_pcd.pessoa)
        self.assertContains(
            r, reverse("avaliacao_medica_detail", args=[self.avaliacao_medica.pk])
        )

        r = self.client.get(f"{url}?tab=nao_avaliadas", follow=True)
        self.assertContains(r, "Avaliações de Documentação Médica")
        self.assertNotContains(r, self.candidato_pcd.pessoa)
        self.assertNotContains(
            r, reverse("avaliacao_medica_add", args=[self.inscricao_pcd.pk])
        )

    def test_fluxo_adicionar_avaliacao_medica(self):
        self.acesso_admin_campus()

        url = reverse("avaliacao_medica_add", args=[self.inscricao_pcd.pk])
        r = self.client.get(url, follow=True)
        self.assertContains(r, "Nova avaliação médica")
        self.assertContains(r, f"<td>{self.candidato_pcd.pessoa}")
        self.assertContains(r, f"<td>{self.inscricao_pcd.edicao}")
        qtde_avaliacoes = models.AvaliacaoDocumental.objects.filter(
            tipo_analise__nome="AVALIAÇÃO MÉDICA"
        ).count()

        self.adicionar_analise()
        data = {
            "tipo_analise": self.tipo_analise_medica.pk,
            "servidor_setor": "Servidor",
            "analise_documental": self.analise_pcd.pk,
            "data": datetime.date(2000, 1, 1),
            "observaçao": "Teste de avaliação médica.",
            "situacao": True,
        }
        r = self.client.post(url, data=data, follow=True)
        self.assertEquals(
            models.AvaliacaoDocumental.objects.filter(
                tipo_analise__nome="AVALIAÇÃO MÉDICA"
            ).count(),
            qtde_avaliacoes + 1,
        )
        self.assertContains(r, "Avaliações de Documentação Médica")
        self.assertContains(
            r, f"Avaliação de {self.candidato_pcd.pessoa} foi criada com sucesso."
        )
        self.assertContains(r, "Busca avançada")

        r = self.client.post(url, data=data, follow=True)
        self.assertEquals(
            models.AvaliacaoDocumental.objects.filter(
                tipo_analise__nome="AVALIAÇÃO MÉDICA"
            ).count(),
            qtde_avaliacoes + 1,
        )
        self.assertNotContains(
            r, f"Avaliação de {self.candidato_pcd.pessoa} foi criada com sucesso."
        )
        self.assertContains(
            r, "Já existe avaliação deste tipo cadastrada para esta inscrição."
        )


class SituacaoInscricaoTestCase(PSTestCase):
    def setUp(self) -> None:
        self.hoje = datetime.date.today()
        self.periodo_convocacao = mommy.make(
            PeriodoConvocacao,
            tipo="CONVOCACAO",
            evento="ANALISE",
            inscricao=False,
            gerenciavel=True,
            etapa=self.etapa,
        )
        self.etapa.publica = True
        self.etapa.save()
        self.dados_chamada = dict(
            etapa=self.etapa,
            multiplicador=3,
            vagas=3,
            curso=self.curso_fisica_subsequente_noturno,
        )
        self.chamada_ampla = mommy.make(
            models.Chamada, modalidade=self.modalidade_ampla, **self.dados_chamada
        )
        self.chamada_cota = mommy.make(
            models.Chamada, modalidade=self.modalidade_cota_racial, **self.dados_chamada
        )
        self.candidato = mommy.make(models.Candidato, pessoa__nome="Candidato A")
        self.dados_inscricao = dict(
            candidato=self.candidato,
            curso=self.curso_fisica_subsequente_noturno,
            edicao=self.edicao,
        )
        self.inscricao_ampla = mommy.make(
            models.Inscricao,
            modalidade=self.modalidade_ampla,
            chamada=self.chamada_ampla,
            **self.dados_inscricao,
        )
        self.inscricao_cota = mommy.make(
            models.Inscricao,
            modalidade=self.modalidade_cota_racial,
            chamada=self.chamada_cota,
            **self.dados_inscricao,
        )
        self.dados_analise = dict(
            servidor_coordenacao=self.pessoa.user,
            observacao="Situação deferida por ....",
            data=self.hoje,
            situacao_final=True,
        )

    def definir_periodo_convocacao_iniciado(self, encerrado=False):
        self.periodo_convocacao.inicio = self.hoje
        self.periodo_convocacao.fim = self.hoje
        if encerrado:
            self.periodo_convocacao.inicio -= datetime.timedelta(days=1)
            self.periodo_convocacao.fim -= datetime.timedelta(days=1)
        self.periodo_convocacao.save()

    def test_situacao_convocado(self):
        self.definir_periodo_convocacao_iniciado(encerrado=False)
        self.assertEqual(
            str(self.inscricao_ampla.get_situacao()), str(models.SituacaoConvocado())
        )

    def test_situacao_nao_definida(self):
        self.definir_periodo_convocacao_iniciado(encerrado=False)
        self.etapa.publica = False
        self.etapa.save()
        self.assertEqual(
            str(self.inscricao_ampla.get_situacao()), str(models.SituacaoNaoDefinida())
        )

    def test_situacao_nao_compareceu(self):
        self.definir_periodo_convocacao_iniciado(encerrado=True)
        self.assertEqual(
            str(self.inscricao_ampla.get_situacao()),
            str(models.SituacaoNaoCompareceu()),
        )

    def test_situacao_aguardando_avaliacao(self):
        self.definir_periodo_convocacao_iniciado(encerrado=True)
        mommy.make(
            models.ConfirmacaoInteresse,
            inscricao=self.inscricao_ampla,
            etapa=self.etapa,
        )
        self.assertEqual(
            str(self.inscricao_ampla.get_situacao()),
            str(models.SituacaoAguardandoAvaliacao()),
        )

    def test_situacao_apto(self):
        self.definir_periodo_convocacao_iniciado(encerrado=True)
        interesse = mommy.make(
            models.ConfirmacaoInteresse,
            inscricao=self.inscricao_ampla,
            etapa=self.etapa,
        )
        dados_analise_indeferida = self.dados_analise.copy()
        dados_analise_indeferida["situacao_final"] = False
        analise = mommy.make(
            models.AnaliseDocumental,
            confirmacao_interesse=interesse,
            **dados_analise_indeferida,
        )
        mommy.make(
            models.Recurso,
            analise_documental=analise,
            status_recurso=models.StatusRecurso.DEFERIDO.value,
        )
        self.assertEqual(
            str(self.inscricao_ampla.get_situacao()), str(models.SituacaoApto())
        )

    def test_situacao_atende_requisitos(self):
        self.definir_periodo_convocacao_iniciado(encerrado=True)
        interesse = mommy.make(
            models.ConfirmacaoInteresse,
            inscricao=self.inscricao_ampla,
            etapa=self.etapa,
        )
        mommy.make(
            models.AnaliseDocumental,
            confirmacao_interesse=interesse,
            **self.dados_analise,
        )
        self.assertEqual(
            str(self.inscricao_ampla.get_situacao()),
            str(models.SituacaoAnaliseDocumental(situacao=True)),
        )

    def test_situacao_indeferido(self):
        self.definir_periodo_convocacao_iniciado(encerrado=True)
        interesse = mommy.make(
            models.ConfirmacaoInteresse,
            inscricao=self.inscricao_ampla,
            etapa=self.etapa,
        )
        dados_analise_indeferida = self.dados_analise.copy()
        dados_analise_indeferida["situacao_final"] = False
        analise = mommy.make(
            models.AnaliseDocumental,
            confirmacao_interesse=interesse,
            **dados_analise_indeferida,
        )
        self.assertEqual(
            str(self.inscricao_ampla.get_situacao()),
            str(models.SituacaoAnaliseDocumental(situacao=False)),
        )
        mommy.make(
            models.Recurso,
            analise_documental=analise,
            status_recurso=models.StatusRecurso.INDEFERIDO.value,
        )
        self.assertEqual(
            str(self.inscricao_ampla.get_situacao()),
            str(models.SituacaoAnaliseDocumental(situacao=False)),
        )

    def test_situacao_matriculado(self):
        mommy.make(models.Matricula, inscricao=self.inscricao_ampla, etapa=self.etapa)
        self.assertEqual(
            str(self.inscricao_ampla.get_situacao()), str(models.SituacaoMatriculado())
        )

    def test_situacao_apto_modalidade_diferente(self):
        self.definir_periodo_convocacao_iniciado(encerrado=True)
        interesse = mommy.make(
            models.ConfirmacaoInteresse,
            inscricao=self.inscricao_ampla,
            etapa=self.etapa,
        )
        mommy.make(
            models.AnaliseDocumental,
            confirmacao_interesse=interesse,
            **self.dados_analise,
        )
        self.assertEqual(
            str(self.inscricao_ampla.get_situacao()),
            str(models.SituacaoAnaliseDocumental(situacao=True)),
        )
        self.assertEqual(
            str(self.inscricao_cota.get_situacao()),
            str(models.SituacaoNaoDefinida(mensagem="Avaliado(a) em outra cota")),
        )

    def test_situacao_matriculado_modalidade_diferente(self):
        mommy.make(models.Matricula, inscricao=self.inscricao_ampla, etapa=self.etapa)
        self.assertEqual(
            str(self.inscricao_cota.get_situacao()),
            str(models.SituacaoMatriculado("Matriculado(a) na lista geral")),
        )


class ProcessoIndexViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.request.user = mock.Mock()
        cls.view = views.ProcessosIndexView()
        cls.view.setup(cls.request)

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.template_name, "processoseletivo/index.html")

    def test_get_context_data_deveria_ter_todos_os_processos_seletivos(self):
        processo1 = recipes.processo_seletivo.make(sigla="PS1")
        processo2 = recipes.processo_seletivo.make(sigla="PS2")
        context = self.view.get_context_data()
        self.assertIn(processo1, context["processos"])
        self.assertIn(processo2, context["processos"])


class EdicoesViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.processo = recipes.processo_seletivo.make()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.request.user = mock.Mock()
        cls.view = views.EdicoesView()
        cls.view.setup(cls.request, processo_pk=cls.processo.id)

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.template_name, "processoseletivo/edicoes.html")

    def test_get_context_data_deveria_ter_processo(self):
        context = self.view.get_context_data()
        self.assertEqual(self.processo, context["processo"])

    def test_get_context_data_deveria_ter_edicoes_abertas(self):
        edicao = recipes.edicao.make(processo_seletivo=self.processo, status="ABERTO")
        context = self.view.get_context_data()
        self.assertIn(edicao, context["edicoes_abertas"])

    def test_edicoes_abertas_em_get_context_data_nao_deveria_ter_edicao_fechada(self):
        edicao = recipes.edicao.make(processo_seletivo=self.processo, status="FECHADO")
        context = self.view.get_context_data()
        self.assertNotIn(edicao, context["edicoes_abertas"])

    def test_get_context_data_deveria_ter_edicoes_encerradas(self):
        edicao = recipes.edicao.make(processo_seletivo=self.processo, status="FECHADO")
        context = self.view.get_context_data()
        self.assertIn(edicao, context["edicoes_encerradas"])

    def test_edicoes_encerradas_em_get_context_data_nao_deveria_ter_edicao_aberta(self):
        edicao = recipes.edicao.make(processo_seletivo=self.processo, status="ABERTO")
        context = self.view.get_context_data()
        self.assertNotIn(edicao, context["edicoes_encerradas"])

    def test_get_context_data_deveria_ter_edicoes_encerradas_paginadas(self):
        recipes.edicao.make(
            processo_seletivo=self.processo, status="FECHADO", _quantity=11
        )
        context = self.view.get_context_data()
        self.assertIn("paginado", context)
        self.assertEqual(10, len(context["edicoes_encerradas"]))


class EdicaoViewTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.processo = recipes.processo_seletivo.make()
        cls.edicao = recipes.edicao.make(processo_seletivo=cls.processo)
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.request.user = mock.Mock()
        cls.view = views.EdicaoView()
        cls.view.setup(
            cls.request, processo_pk=cls.processo.id, edicao_pk=cls.edicao.id
        )

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.template_name, "processoseletivo/edicao.html")

    def test_get_context_data_deveria_ter_processo(self):
        context = self.view.get_context_data()
        self.assertEqual(self.processo, context["processo"])

    def test_get_context_data_deveria_ter_edicao(self):
        context = self.view.get_context_data()
        self.assertEqual(self.edicao, context["edicao"])

    def test_get_context_data_deveria_ter_edital_de_abertura(self):
        edital = mommy.make(
            "editais.Edital",
            edicao=self.edicao,
            publicado=True,
            tipo="ABERTURA",
            descricao="Edital de abertura",
        )
        mommy.make("editais.Edital", edicao=self.edicao, descricao="Outro edital")
        context = self.view.get_context_data()
        self.assertEqual(edital, context["edital"])

    def test_get_context_data_deveria_exibir_prazo_falso(self):
        edital = mommy.make(
            "editais.Edital",
            edicao=self.edicao,
            publicado=True,
            tipo="ABERTURA",
            descricao="Edital de abertura",
        )
        mommy.make(
            "editais.NivelSelecao",
            edital=edital,
            valor_inscricao=0,
        )
        context = self.view.get_context_data()
        self.assertFalse(context["exibe_prazo"])

    def test_get_context_data_deveria_exibir_prazo_verdadeiro(self):
        edital = mommy.make(
            "editais.Edital",
            edicao=self.edicao,
            publicado=True,
            tipo="ABERTURA",
            descricao="Edital de abertura",
        )
        mommy.make(
            "editais.NivelSelecao",
            edital=edital,
            valor_inscricao=10,
        )
        context = self.view.get_context_data()
        self.assertTrue(context["exibe_prazo"])

    def test_get_context_data_deveria_ter_etapa_unica(self):
        etapa = recipes.etapa.make(edicao=self.edicao, numero=0)
        context = self.view.get_context_data()
        self.assertEqual(etapa, context["etapa_resultado_unica"])

    def test_get_context_data_nao_deveria_ter_etapa_unica(self):
        recipes.etapa.make(edicao=self.edicao)
        recipes.etapa.make(edicao=self.edicao)
        context = self.view.get_context_data()
        self.assertIsNone(context["etapa_resultado_unica"])

    def test_get_context_data_deveria_ter_etapa_resultado_em_andamento(self):
        recipes.etapa.make(edicao=self.edicao, numero=0)
        context = self.view.get_context_data()
        self.assertTrue(context["etapa_resultado_andamento"])

    def test_get_context_data_deveria_ter_etapa_resultado_publicada(self):
        recipes.etapa.make(edicao=self.edicao, numero=0, publica=True)
        context = self.view.get_context_data()
        self.assertTrue(context["etapas_resultado_publicadas"])

    def test_get_context_data_deveria_ter_etapa_espera_para_cada_campus_da_etapa(self):
        campus_jp = mommy.make("cursos.Campus", nome="JP")
        campus_cg = mommy.make("cursos.Campus", nome="CG")
        etapa_jp = recipes.etapa.make(
            edicao=self.edicao, numero=1, publica=True, campus=campus_jp
        )
        etapa_cg = recipes.etapa.make(
            edicao=self.edicao, numero=1, publica=True, campus=campus_cg
        )
        context = self.view.get_context_data()
        self.assertIn(etapa_jp, context["etapa_espera_campus"]["JP"])
        self.assertIn(etapa_cg, context["etapa_espera_campus"]["CG"])


class EtapasViewParametroEdicaoTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.edicao = recipes.edicao.make()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.request.user = mock.Mock()
        cls.view = views.EtapasView()
        cls.view.setup(cls.request, edicao_pk=cls.edicao.id)

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.template_name, "processoseletivo/etapas.html")

    def test_get_context_data_deveria_ter_edicao(self):
        context = self.view.get_context_data()
        self.assertEqual(self.edicao, context["edicao"])

    def test_get_context_data_deveria_ter_processo(self):
        context = self.view.get_context_data()
        self.assertEqual(self.edicao.processo_seletivo, context["processo"])

    def test_get_context_data_deveria_ter_etapas_paginadas(self):
        recipes.etapa.make(edicao=self.edicao, publica=True, _quantity=11)
        context = self.view.get_context_data()
        self.assertIn("paginado", context)
        self.assertEqual(10, len(context["etapas"]))


class EtapasViewParametroProcessoTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.processo = recipes.processo_seletivo.make()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.request.user = mock.Mock()
        cls.view = views.EtapasView()
        cls.view.setup(cls.request, processo_pk=cls.processo.id)

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.template_name, "processoseletivo/etapas.html")

    def test_get_context_data_deveria_ter_processo(self):
        context = self.view.get_context_data()
        self.assertEqual(self.processo, context["processo"])

    def test_get_context_data_deveria_ter_etapas_paginadas(self):
        edicao = recipes.edicao.make(processo_seletivo=self.processo)
        recipes.etapa.make(edicao=edicao, publica=True, _quantity=11)
        context = self.view.get_context_data()
        self.assertIn("paginado", context)
        self.assertEqual(10, len(context["etapas"]))


class EtapasViewFuncionalTestCase(TestCase):
    def test_qualquer_usuario_deve_conseguir_acessar_a_pagina_com_parametro_edicao(self):
        edicao = recipes.edicao.make()
        response = self.client.get(reverse("etapas", args=[edicao.id]))
        self.assertEqual(200, response.status_code)

    def test_qualquer_usuario_deve_conseguir_acessar_a_pagina_com_parametro_processo_seletivo(self):
        processo_seletivo = recipes.processo_seletivo.make()
        response = self.client.get(reverse("etapas_ps", args=[processo_seletivo.id]))
        self.assertEqual(200, response.status_code)


class EtapasResultadoViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.view = views.EtapasResultadoView()
        cls.edicao = recipes.edicao.make()
        cls.view.setup(cls.request, edicao_pk=cls.edicao.id)
        cls.grupo_campi_chamadas = Group.objects.create(name=models.GRUPO_CAMPI)

    def setUp(self) -> None:
        super().setUp()
        self.user = base.tests.recipes.user.make()
        self.request.user = self.user

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            self.view.template_name, "processoseletivo/etapas_resultado.html"
        )

    def test_get_context_data_deveria_ter_edicao(self):
        context = self.view.get_context_data(edicao_pk=self.edicao.id)
        self.assertEqual(self.edicao, context["edicao"])

    def test_get_context_data_deveria_ter_etapas_com_numero_zero(self):
        etapa1 = recipes.etapa.make(edicao=self.edicao, numero=0)
        etapa2 = recipes.etapa.make(edicao=self.edicao, numero=0)
        context = self.view.get_context_data(edicao_pk=self.edicao.id)
        self.assertIn(etapa1, context["etapas"])
        self.assertIn(etapa2, context["etapas"])

    def test_get_context_data_nao_deveria_ter_etapas_com_numero_diferente_de_zero(self):
        etapa = recipes.etapa.make(edicao=self.edicao)
        context = self.view.get_context_data(edicao_pk=self.edicao.id)
        self.assertNotIn(etapa, context["etapas"])

    def test_get_context_data_deveria_retornar_verdadeiro_para_etapa_publicada(self):
        etapa = recipes.etapa.make(edicao=self.edicao, publica=True)
        context = self.view.get_context_data(edicao_pk=self.edicao.id)
        self.assertNotIn(etapa, context["etapas"])

    def test_test_get_context_data_deveria_retornar_falso_para_permissao_do_usuario(
        self,
    ):
        context = self.view.get_context_data(edicao_pk=self.edicao.id)
        self.assertFalse(context["admin_permission"])

    def test_test_get_context_data_deveria_retornar_verdadeiro_para_permissao_do_usuario(
        self,
    ):
        self.user.groups.add(self.grupo_campi_chamadas)
        context = self.view.get_context_data(edicao_pk=self.edicao.id)
        self.assertTrue(context["admin_permission"])

class ImportacaoViewTestCase(TestCase):
    fixtures = ["modalidade.json"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.view = views.ImportacaoView()
        cls.edicao = recipes.edicao.make(ano=2020)
        cls.view.setup(cls.request, pk=cls.edicao.id)
        cls.grupo_sistemico_chamadas = Group.objects.create(name=models.GRUPO_SISTEMICO)
        cls.grupo_campi_chamadas = Group.objects.create(name=models.GRUPO_CAMPI)
        cls.modalidade = models.Modalidade.objects.get(
            pk=models.ModalidadeEnum.cota_racial
        )

    def setUp(self) -> None:
        super().setUp()
        self.user = base.tests.recipes.user.make()
        self.user.groups.add(self.grupo_sistemico_chamadas)
        self.request.user = self.user
        self.view.edicao = self.edicao
        self.view.modalidades = [self.modalidade]

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.template_name, "processoseletivo/importacao.html")

    def test_user_sem_permissao_sistemica_nao_deveria_acessar_view(self):
        user = base.tests.recipes.user.make()
        user.groups.add(self.grupo_campi_chamadas)
        self.request.user = user
        self.assertFalse(self.view.has_permission())

    def test_get_form_kwargs_deveriar_ter_modalidades(self):
        kwargs = self.view.get_form_kwargs()
        self.assertIn(self.modalidade, kwargs["modalidades"])

    @mock.patch("django.contrib.messages.info")
    def test_get_success_url_deveria_retornar_url_do_job(self, messages):
        messages.return_value = None
        job = mock.Mock()
        job.get_absolute_url.return_value = "/admin"
        self.view.job = job
        self.assertEqual("/admin", self.view.get_success_url())

    def test_get_context_data_deveria_ter_titulo(self):
        context = self.view.get_context_data()
        self.assertEqual("Importar dados do PS1 2020 - Edição 1", context["titulo"])

    def test_get_context_data_deveria_ter_modalidades(self):
        context = self.view.get_context_data()
        self.assertEqual([self.modalidade], context["modalidades"])


class CreateChamadaViewTestCase(DiretorEnsinoPermissionData, UserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.view = views.CreateChamadaView()
        cls.grupo_sistemico_chamadas = Group.objects.create(name=models.GRUPO_SISTEMICO)

    def setUp(self) -> None:
        super().setUp()
        self.usuario_base.groups.add(self.grupo_sistemico_chamadas)
        self.request.user = self.usuario_base
        self.etapa = recipes.etapa.make()
        self.view.setup(self.request, etapa_pk=self.etapa.id)

    @mock.patch("processoseletivo.models.Edicao.pode_importar")
    def test_user_sem_permissao_nao_deveria_acessar_view(self, pode_importar):
        pode_importar.return_value = True
        user = base.tests.recipes.user.make()
        self.request.user = user
        self.assertFalse(self.view.has_permission())

    @mock.patch("processoseletivo.models.Edicao.get_modalidades_para_importacao")
    @mock.patch("processoseletivo.models.Edicao.pode_importar")
    def test_user_com_permissao_de_campus_deveria_acessar_view(
        self, pode_importar, get_modalidades
    ):
        pode_importar.return_value = True
        get_modalidades.return_value = None
        self.assertTrue(self.view.has_permission())

    def test_nao_deveria_gerar_chamada_com_etapa_encerrada(self):
        etapa = recipes.etapa.make(encerrada=True)
        self.client.logout()
        self.client.login(username=self.usuario_base.username, password="123")
        response = self.client.get(
            reverse("adicionar_chamadas", args=[etapa.id]), follow=True
        )
        self.assertEqual(
            list(response.context["messages"])[0].message,
            "Você não pode gerar chamadas para uma etapa encerrada",
        )

    def test_nao_deveria_gerar_chamada_com_chamadas_ja_realizadas(self):
        self.client.logout()
        self.client.login(username=self.usuario_base.username, password="123")
        recipes.chamada.make(etapa=self.etapa)
        response = self.client.get(
            reverse("adicionar_chamadas", args=[self.etapa.id]), follow=True
        )
        self.assertEqual(
            list(response.context["messages"])[0].message,
            "Já existem chamadas definidas",
        )

    @mock.patch("processoseletivo.views.tasks.gerar_chamada_ps")
    def test_deveria_gerar_chamada(self, task):
        task.return_value = None
        self.client.logout()
        self.client.login(username=self.usuario_base.username, password="123")
        response = self.client.get(
            reverse("adicionar_chamadas", args=[self.etapa.id]), follow=True
        )
        self.assertEqual(
            list(response.context["messages"])[0].message,
            "Esta operação irá demorar vários minutos, você receberá um email quando ela estiver concluída",
        )


class AddCandidatosViewTestCase(DiretorEnsinoPermissionData, UserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.view = views.AddCandidatosView()
        cls.etapa = recipes.etapa.make()
        cls.grupo_sistemico_chamadas = Group.objects.create(name=models.GRUPO_SISTEMICO)
        cls.grupo_campi_chamadas = Group.objects.create(name=models.GRUPO_CAMPI)

    def setUp(self) -> None:
        super().setUp()
        self.usuario_base.groups.add(self.grupo_sistemico_chamadas)
        self.request.user = self.usuario_base
        self.chamada = recipes.chamada.make(etapa=self.etapa)
        self.view.setup(self.request, chamada_pk=self.chamada.id)

    def test_user_sem_permissao_nao_deveria_acessar_view(self):
        user = base.tests.recipes.user.make()
        self.request.user = user
        self.assertFalse(self.view.has_permission())

    def test_user_sistemico_nao_deveria_ter_permissao_em_view_com_etapa_de_resultado(
        self,
    ):
        etapa = recipes.etapa.make(numero=0)
        chamada = recipes.chamada.make(etapa=etapa)
        self.view.setup(self.request, chamada_pk=chamada.id)
        self.assertFalse(self.view.has_permission())

    def test_user_de_campus_nao_deveria_ter_permissao_em_view_com_etapa_de_outro_campus(
        self,
    ):
        user = base.tests.recipes.user.make()
        user.groups.add(self.grupo_campi_chamadas)
        self.request.user = user
        self.assertFalse(self.view.has_permission())

    def test_user_sistemico_deveria_ter_permissao_para_acessar_view(self):
        self.assertTrue(self.view.has_permission())

    def test_nao_deveriar_adicionar_candidato_com_confirmacao(self):
        self.client.logout()
        self.client.login(**self.usuario_base.credentials)
        inscricao = recipes.inscricao.make(chamada=self.chamada)
        recipes.confirmacao.make(inscricao=inscricao)
        response = self.client.post(
            reverse("adicionar_candidatos", args=[self.chamada.id]), follow=True
        )
        self.assertEqual(
            list(response.context["messages"])[0].message,
            "Não é permitido adicionar candidatos a uma chamada que possui confirmações de interesse cadastradas.",
        )

    def test_deveriar_adicionar_candidato(self):
        self.client.logout()
        self.client.login(**self.usuario_base.credentials)
        response = self.client.post(
            reverse("adicionar_candidatos", args=[self.chamada.id]), follow=True
        )
        self.assertEqual(
            list(response.context["messages"])[0].message,
            "Candidatos adicionados com sucesso",
        )


class AjaxViewTestCase(DiretorEnsinoPermissionData, TestCase):
    fixtures = ["modalidade.json"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.view = views.AjaxView()
        cls.etapa = recipes.etapa.make()
        cls.grupo_sistemico_chamadas = Group.objects.create(name=models.GRUPO_SISTEMICO)
        cls.grupo_campi_chamadas = Group.objects.create(name=models.GRUPO_CAMPI)
        cls.modalidade = models.Modalidade.objects.get(
            pk=models.ModalidadeEnum.cota_racial
        )
        cls.inscricao = recipes.inscricao.make(
            edicao=cls.etapa.edicao, modalidade=cls.modalidade
        )

    def setUp(self) -> None:
        super().setUp()
        self.user = base.tests.recipes.user.make()
        self.user.groups.add(self.grupo_sistemico_chamadas)
        self.request.user = self.user
        self.view.setup(
            self.request,
            candidato_pk=self.inscricao.candidato.id,
            modalidade_pk=self.modalidade.id,
            etapa_pk=self.etapa.pk,
        )

    def test_user_sem_permissao_nao_deveria_acessar_view(self):
        user = base.tests.recipes.user.make()
        self.request.user = user
        self.assertFalse(self.view.has_permission())

    def test_user_de_grupo_campi_deveria_acessar_view(self):
        user = base.tests.recipes.user.make()
        user.groups.add(self.grupo_campi_chamadas)
        self.request.user = user
        self.assertTrue(self.view.has_permission())

    def test_user_de_grupo_sistemico_deveria_acessar_view(self):
        self.assertTrue(self.view.has_permission())

    @mock.patch("processoseletivo.views.AjaxView.do_action")
    def test_retornar_response_ok(self, do_action):
        do_action.return_value = None
        response = self.view.post(self.request)
        self.assertEqual('{"ok": true}', response.content.decode())


class MatriculaViewTestCase(DiretorEnsinoPermissionData, TestCase):
    fixtures = ["modalidade.json"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view = views.MatricularView()
        cls.modalidade = models.Modalidade.objects.get(
            pk=models.ModalidadeEnum.cota_racial
        )
        cls.etapa = recipes.etapa.make()
        cls.chamada = recipes.chamada.make(modalidade=cls.modalidade, etapa=cls.etapa)
        cls.vaga = recipes.vaga.make(
            edicao=cls.etapa.edicao, modalidade=cls.modalidade, candidato=None
        )

    def test_deveria_matricula_inscricao(self):
        inscricao = recipes.inscricao.make(
            edicao=self.etapa.edicao,
            modalidade=self.modalidade,
            chamada=self.chamada,
            curso=self.vaga.curso,
        )
        self.view.etapa = self.etapa
        self.view.inscricao = inscricao
        self.view.do_action()
        self.assertTrue(models.Matricula.objects.filter(inscricao=inscricao).exists())


class CancelamentoMatriculaViewTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view = views.CancelarMatriculaView()
        cls.matricula = recipes.matricula.make()
        cls.view.etapa = cls.matricula.etapa
        cls.view.inscricao = cls.matricula.inscricao

    def test_deveria_cancelar_matricula(self):
        self.view.do_action()
        self.assertFalse(models.Matricula.objects.filter(id=self.matricula.id).exists())


class RelatorioConvocadosViewTestCase(UserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.etapa = recipes.etapa.make()
        cls.view = views.RelatorioConvocadosPorCotaView()
        cls.grupo_sistemico_chamadas = Group.objects.create(name=models.GRUPO_SISTEMICO)
        cls.view.setup(cls.request, etapa_pk=cls.etapa.id)

    def setUp(self) -> None:
        super().setUp()
        self.usuario_base.groups.add(self.grupo_sistemico_chamadas)
        self.request.user = self.usuario_base
        self.view.request = self.request

    def test_user_sem_permissao_nao_deveria_acessar_view(self):
        user = base.tests.recipes.user.make()
        self.request.user = user
        self.assertFalse(self.view.has_permission())

    @mock.patch("processoseletivo.views.tasks.relatorio_convocados_por_cota_pdf")
    def test_deveriar_processar_relatorio(self, task):
        task.return_value = None
        self.client.logout()
        self.client.login(username=self.usuario_base.username, password="123")
        response = self.client.get(
            reverse("relatorio-convocados-por-cota", args=[self.etapa.id]), follow=True
        )
        self.assertEqual(
            list(response.context["messages"])[0].message,
            "Sua solicitação está sendo processada. Você receberá o arquivo em seu e-mail.",
        )


class RelatorioMatriculadosViewTestCase(UserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.etapa = recipes.etapa.make()
        cls.view = views.RelatorioMatriculadosView()
        cls.grupo_sistemico_chamadas = Group.objects.create(name=models.GRUPO_SISTEMICO)
        cls.view.setup(cls.request, etapa_pk=cls.etapa.id)

    def setUp(self) -> None:
        super().setUp()
        self.usuario_base.groups.add(self.grupo_sistemico_chamadas)
        self.request.user = self.usuario_base
        self.view.request = self.request

    def test_user_sem_permissao_nao_deveria_acessar_view(self):
        user = base.tests.recipes.user.make()
        self.request.user = user
        self.assertFalse(self.view.has_permission())

    @mock.patch("processoseletivo.views.tasks.relatorio_matriculados_xlsx")
    def test_deveria_processar_relatorio(self, task):
        task.return_value = None
        self.client.logout()
        self.client.login(username=self.usuario_base.username, password="123")
        response = self.client.get(
            reverse("relatorio_matriculados", args=[self.etapa.id]), follow=True
        )
        self.assertEqual(
            list(response.context["messages"])[0].message,
            "Sua solicitação está sendo processada. Você receberá o arquivo em seu email.",
        )


class AnaliseDocumentoEtapaViewTestCase(UserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.etapa = recipes.etapa.make()
        cls.view = views.AnaliseDocumentoEtapaView()
        cls.grupo_sistemico_chamadas = Group.objects.create(name=models.GRUPO_SISTEMICO)
        cls.view.setup(cls.request, etapa_pk=cls.etapa.id)

    def setUp(self) -> None:
        super().setUp()
        self.usuario_base.groups.add(self.grupo_sistemico_chamadas)
        self.request.user = self.usuario_base
        self.view.request = self.request

    def test_user_sem_permissao_nao_deveria_acessar_view(self):
        user = base.tests.recipes.user.make()
        self.request.user = user
        self.assertFalse(self.view.has_permission())

    @mock.patch("processoseletivo.views.tasks.analise_documental_etapa_pdf")
    def test_deveriar_gerar_lista_de_analise_documental(self, task):
        task.return_value = None
        self.client.logout()
        self.client.login(**self.usuario_base.credentials)
        response = self.client.get(
            reverse("gerar_lista_analise_documental", args=[self.etapa.id]), follow=True
        )
        self.assertEqual(
            list(response.context["messages"])[0].message,
            "Sua solicitação está sendo processada. Você receberá o arquivo em seu email.",
        )


class ListagemFinalViewTestCase(UserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.etapa = recipes.etapa.make(encerrada=True)
        cls.view = views.ListagemFinalView()
        cls.grupo_sistemico_chamadas = Group.objects.create(name=models.GRUPO_SISTEMICO)

    def setUp(self) -> None:
        super().setUp()
        self.usuario_base.groups.add(self.grupo_sistemico_chamadas)
        self.request.user = self.usuario_base
        self.view.request = self.request
        self.view.setup(self.request, etapa_pk=self.etapa.id)

    def test_user_sem_permissao_nao_deveria_acessar_view(self):
        user = base.tests.recipes.user.make()
        self.request.user = user
        self.assertFalse(self.view.has_permission())

    def test_user_nao_deveriar_ter_permissao_criar_lista_final_de_etapa_aberta(self):
        etapa = recipes.etapa.make()
        self.view.setup(self.request, etapa_pk=etapa.id)
        self.assertFalse(self.view.has_permission())

    @mock.patch("django.contrib.messages.info")
    @mock.patch("processoseletivo.views.ListagemFinalView.get_relatorio")
    def test_deveriar_gerar_lista_final(self, task, messages):
        messages.info.return_value = None
        task.return_value.task.return_value = None
        response = self.view.get(self.request)
        self.assertEqual(
            response.url,
            reverse("admin:processoseletivo_etapa_change", args=[self.etapa.id]),
        )


class ReaberturaEtapaViewTestCase(UserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.etapa = recipes.etapa.make(encerrada=True)
        cls.view = views.ReabrirEtapalView()
        cls.grupo_sistemico_chamadas = Group.objects.create(name=models.GRUPO_SISTEMICO)

    def setUp(self) -> None:
        super().setUp()
        self.usuario_base.groups.add(self.grupo_sistemico_chamadas)
        self.request.user = self.usuario_base
        self.view.request = self.request
        self.view.setup(self.request, etapa_pk=self.etapa.id)

    def test_user_sem_permissao_nao_deveria_acessar_view(self):
        user = base.tests.recipes.user.make()
        self.request.user = user
        self.assertFalse(self.view.has_permission())

    def test_nao_deveria_reabrir_etapa_nao_encerrada(self):
        etapa = recipes.etapa.make()
        self.view.setup(self.request, etapa_pk=etapa.id)
        self.assertFalse(self.view.has_permission())

    @mock.patch("processoseletivo.views.tasks.reabrir_etapa")
    @mock.patch("monitoring.models.Job.new")
    def test_deveriar_reabrir_etapa(self, job, reabrir_etapa):
        new_job = mock.Mock()
        new_job.get_absolute_url.return_value = ".."
        job.return_value = new_job
        reabrir_etapa.return_value = None
        self.client.logout()
        self.client.login(username=self.usuario_base.username, password="123")
        response = self.client.get(
            reverse("reabrir_etapa", args=[self.etapa.id]), follow=True
        )
        self.assertEqual(
            list(response.context["messages"])[0].message,
            "Sua solicitação está sendo processada. Aguarde alguns instantes.",
        )


class FormulariosAnaliseDocumentoViewTestCase(
    DiretorEnsinoPermissionData, UserTestMixin, TestCase
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.chamada = recipes.chamada.make()
        cls.view = views.FormulariosAnaliseDocumentoView()
        cls.grupo_sistemico_chamadas = Group.objects.create(name=models.GRUPO_SISTEMICO)

    def setUp(self) -> None:
        super().setUp()
        self.usuario_base.groups.add(self.grupo_sistemico_chamadas)
        self.request.user = self.usuario_base
        self.view.request = self.request
        self.view.setup(self.request, chamada_pk=self.chamada.id)

    def test_user_sem_permissao_nao_deveria_acessar_view(self):
        user = base.tests.recipes.user.make()
        self.request.user = user
        self.assertFalse(self.view.has_permission())

    @mock.patch("processoseletivo.views.tasks.formulario_analise_documental_pdf")
    def test_deveriar_gerar_analise_documental(self, analise):
        analise.return_value = None
        self.client.logout()
        self.client.login(**self.usuario_base.credentials)
        inscricao = recipes.inscricao.make(chamada=self.chamada)
        recipes.confirmacao.make(inscricao=inscricao)
        response = self.client.get(
            reverse("gerar_forms_analise_documento", args=[self.chamada.id]),
            follow=True,
        )
        self.assertEqual(
            list(response.context["messages"])[0].message,
            "Sua solicitação está sendo processada. Você receberá o arquivo em seu email.",
        )

    @mock.patch("processoseletivo.views.tasks.formulario_analise_documental_pdf")
    def test_nao_deveriar_gerar_analise_documental_sem_confirmacao_na_chamada(
        self, analise
    ):
        analise.return_value = None
        self.client.logout()
        self.client.login(username=self.usuario_base.username, password="123")
        recipes.inscricao.make(chamada=self.chamada)
        response = self.client.get(
            reverse("gerar_forms_analise_documento", args=[self.chamada.id]),
            follow=True,
        )
        self.assertEqual(
            list(response.context["messages"])[0].message,
            "Os formulários não podem ser gerados pois não há confirmações de interesse para esta chamada.",
        )


class VagasViewTestCase(DiretorEnsinoPermissionData, UserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.edicao = recipes.edicao.make()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.view = views.VagasView()
        cls.grupo_sistemico = Group.objects.create(name="Administradores Sistêmicos")

    def setUp(self) -> None:
        super().setUp()
        self.request.user = self.usuario_base
        self.view.setup(self.request, pk=self.edicao.id)

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.template_name, "processoseletivo/vagas.html")

    def test_user_sem_permissao_nao_deveria_acessar_view(self):
        self.assertFalse(self.view.has_permission())

    def test_administrador_sistemico_deveria_acessar_view(self):
        self.usuario_base.groups.add(self.grupo_sistemico)
        self.assertTrue(self.view.has_permission())

    def test_get_context_data_deveria_ter_edicao(self):
        context = self.view.get_context_data()
        self.assertEqual(self.edicao, context["edicao"])

    def test_get_context_data_deveria_ter_total_vagas(self):
        recipes.vaga.make(edicao=self.edicao)
        context = self.view.get_context_data()
        self.assertEqual(1, context["total_vagas"])

    def test_get_context_data_deveria_ter_informacoes_do_curso(self):
        curso = mommy.make("cursos.CursoSelecao")
        modalidade = mommy.make("processoseletivo.Modalidade", nome="PCD")
        recipes.inscricao.make(edicao=self.edicao, curso=curso)
        recipes.vaga.make(edicao=self.edicao, curso=curso, modalidade=modalidade)
        context = self.view.get_context_data()
        self.assertIn("cursos", context)
        self.assertEqual(str(curso), str(context["cursos"][0][0]))
        self.assertIn(["PCD", 1], context["cursos"][0][1])


class RelatorioResultadoViewTestCase(UserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.edicao = recipes.edicao.make()
        cls.view = views.RelatorioResultadoView()
        cls.grupo_sistemico_chamadas = Group.objects.create(name=models.GRUPO_SISTEMICO)
        cls.view.setup(cls.request, pk=cls.edicao.id)

    def setUp(self) -> None:
        super().setUp()
        self.usuario_base.groups.add(self.grupo_sistemico_chamadas)
        self.request.user = self.usuario_base
        self.view.request = self.request

    def test_user_sem_permissao_nao_deveria_acessar_view(self):
        user = base.tests.recipes.user.make()
        self.request.user = user
        self.assertFalse(self.view.has_permission())

    @mock.patch("processoseletivo.views.tasks.relatorio_resultado_csv")
    def test_deveriar_gerar_relatorio_resultado(self, task):
        task.return_value = None
        self.client.logout()
        self.client.login(**self.usuario_base.credentials)
        response = self.client.get(
            reverse("relatorio_resultado_ps", args=[self.edicao.id]), follow=True
        )
        self.assertEqual(
            list(response.context["messages"])[0].message,
            "Sua solicitação está sendo processada. Você receberá o arquivo em seu email.",
        )


class ReplicarAnaliseDocumentalViewTestCase(
    DiretorEnsinoPermissionData, UserTestMixin, TestCase
):
    fixtures = ["modalidade.json"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.view = views.ReplicarAnaliseDocumentalView()
        cls.grupo_sistemico = Group.objects.create(name=models.GRUPO_SISTEMICO)
        cls.racial = models.Modalidade.objects.get(pk=models.ModalidadeEnum.cota_racial)
        cls.ampla = models.Modalidade.objects.get(
            pk=models.ModalidadeEnum.ampla_concorrencia
        )
        cls.inscricao = recipes.inscricao.make(modalidade=cls.racial)
        confirmacao = recipes.confirmacao.make(
            inscricao=cls.inscricao, etapa=cls.inscricao.chamada.etapa
        )
        cls.analise_indeferida = recipes.analise.make(
            confirmacao_interesse=confirmacao, situacao_final=False
        )

    def setUp(self) -> None:
        super().setUp()
        self.usuario_base.groups.add(self.grupo_sistemico)
        self.request.user = self.usuario_base
        self.view.analise_indeferida = self.analise_indeferida
        self.view.setup(self.request, analise_pk=self.analise_indeferida.id)

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.template_name, "reuse/confirmacao.html")

    def test_user_sem_permissao_nao_deveria_acessar_view(self):
        user = base.tests.recipes.user.make()
        self.request.user = user
        self.assertFalse(self.view.has_permission())

    def test_user_em_grupo_sistemico_deveria_acessar_view(self):
        self.assertTrue(self.view.has_permission())

    def test_get_context_data_deveria_ter_back_url(self):
        context = self.view.get_context_data()
        self.assertEqual(
            context["back_url"],
            reverse(
                "admin:processoseletivo_analisedocumental_change",
                args=[self.analise_indeferida.pk],
            ),
        )

    def test_get_context_data_deveria_ter_titulo(self):
        context = self.view.get_context_data()
        self.assertEqual(
            context["titulo"],
            "Deseja replicar a análise de documentos do(a) candidato(a) "
            f"{self.analise_indeferida.confirmacao_interesse.inscricao.candidato} e criar a análise de Ampla Concorrência?",
        )

    def test_nao_deveria_replicar_analise_quando_existir_confirmacao(self):
        chamada = recipes.chamada.make(etapa=self.inscricao.chamada.etapa)
        inscricao = recipes.inscricao.make(
            candidato=self.inscricao.candidato, chamada=chamada, modalidade=self.ampla
        )
        confirmacao = recipes.confirmacao.make(inscricao=inscricao, etapa=chamada.etapa)
        recipes.analise.make(confirmacao_interesse=confirmacao)
        with self.assertRaises(models.AnaliseDocumental.AlreadyExists) as ex:
            self.view.replicar_analise()

        self.assertIn(
            "Não é possível recriar um objeto já existente.", ex.exception.args
        )

    def test_deveria_replicar_analise(self):
        chamada = recipes.chamada.make(etapa=self.inscricao.chamada.etapa)
        inscricao = recipes.inscricao.make(
            candidato=self.inscricao.candidato, chamada=chamada, modalidade=self.ampla
        )
        self.view.replicar_analise()
        self.assertIsNotNone(inscricao.confirmacaointeresse)

    def test_analise_documental_deveria_ser_criada(self):
        chamada = recipes.chamada.make(etapa=self.inscricao.chamada.etapa)
        recipes.inscricao.make(
            candidato=self.inscricao.candidato, chamada=chamada, modalidade=self.ampla
        )
        self.client.logout()
        self.client.login(**self.usuario_base.credentials)
        response = self.client.post(
            reverse("replicar_analise_documental", args=[self.analise_indeferida.id]),
            follow=True,
        )
        self.assertEqual(
            "Análise Documental criada com sucesso.",
            list(response.context["messages"])[0].message,
        )


class AvaliacaoDocumentalListViewTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view = views.AvaliacaoDocumentalListView()

    def test_template_deveria_estar_corretamente_configurado(self):
        self.assertEqual(self.view.template_name, "reuse/listview.html")

    def test_deveria_retornar_campus(self):
        confirmacao = recipes.confirmacao.make()
        self.assertEqual(
            confirmacao.inscricao.curso.campus.nome, self.view.campus(confirmacao)
        )

    def test_deveria_retornar_candidato(self):
        confirmacao = recipes.confirmacao.make()
        self.assertEqual(
            confirmacao.inscricao.candidato.pessoa, self.view.candidato(confirmacao)
        )

    def test_deveria_retornar_edicao(self):
        confirmacao = recipes.confirmacao.make()
        self.assertEqual(confirmacao.inscricao.edicao, self.view.edicao(confirmacao))

    def test_situacao_deveria_retornar_aguardando(self):
        confirmacao = recipes.confirmacao.make()
        expected = '<span class="status status-pendente">Aguardando Avaliação</span>'
        self.assertEqual(expected, self.view.situacao(confirmacao))

    @mock.patch(
        "processoseletivo.views.AvaliacaoDocumentalListView.tipo_analise",
        new_callable=mock.PropertyMock,
    )
    def test_situacao_deveria_retornar_deferido(self, tipo_analise):
        tipo_analise.return_value = "Tipo de análise 1"
        avaliacao = recipes.avaliacao.make()
        expected = '<span class="status status-deferido">Deferido</span>'
        self.assertEqual(
            expected,
            self.view.situacao(avaliacao.analise_documental.confirmacao_interesse),
        )

    @mock.patch(
        "processoseletivo.views.AvaliacaoDocumentalListView.tipo_analise",
        new_callable=mock.PropertyMock,
    )
    def test_situacao_deveria_retornar_indeferido(self, tipo_analise):
        tipo_analise.return_value = "Tipo de análise 1"
        avaliacao = recipes.avaliacao.make(situacao=False)
        expected = '<span class="status status-indeferido">Indeferido</span>'
        self.assertEqual(
            expected,
            self.view.situacao(avaliacao.analise_documental.confirmacao_interesse),
        )

    @mock.patch(
        "processoseletivo.views.AvaliacaoDocumentalListView.tipo_analise",
        new_callable=mock.PropertyMock,
    )
    def test_deveria_retornar_nenhuma_confirmacao_nao_avaliada(self, tipo_analise):
        tipo_analise.return_value = "Tipo de análise 1"
        recipes.avaliacao.make()
        self.assertFalse(
            self.view.nao_avaliadas(models.ConfirmacaoInteresse.objects.all()).exists()
        )

    @mock.patch(
        "processoseletivo.views.AvaliacaoDocumentalListView.tipo_analise",
        new_callable=mock.PropertyMock,
    )
    def test_deveria_retornar_uma_confirmacao_nao_avaliada(self, tipo_analise):
        tipo_analise.return_value = "Tipo de análise 2"
        recipes.avaliacao.make()
        self.assertTrue(
            self.view.nao_avaliadas(models.ConfirmacaoInteresse.objects.all()).exists()
        )

    @mock.patch(
        "processoseletivo.views.AvaliacaoDocumentalListView.tipo_analise",
        new_callable=mock.PropertyMock,
    )
    def test_deveria_retornar_nenhuma_confirmacao_avaliada(self, tipo_analise):
        tipo_analise.return_value = "Tipo de análise 1"
        recipes.avaliacao.make()
        self.assertTrue(
            self.view.avaliadas(models.ConfirmacaoInteresse.objects.all()).exists()
        )

    @mock.patch(
        "processoseletivo.views.AvaliacaoDocumentalListView.tipo_analise",
        new_callable=mock.PropertyMock,
    )
    def test_deveria_retornar_uma_confirmacao_avaliada(self, tipo_analise):
        tipo_analise.return_value = "Tipo de análise 2"
        recipes.avaliacao.make()
        self.assertFalse(
            self.view.avaliadas(models.ConfirmacaoInteresse.objects.all()).exists()
        )


class AvaliacaoMedicaListViewTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view = views.AvaliacaoMedicaListView()

    def test_tipo_analise_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            models.TipoAnalise.TIPO_AVALIACAO_MEDICA, self.view.tipo_analise
        )

    def test_add_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual("avaliacao_medica_add", self.view.add_url)

    def test_change_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual("avaliacao_medica_update", self.view.change_url)

    def test_delete_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual("avaliacao_medica_delete", self.view.delete_url)

    def test_detail_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual("avaliacao_medica_detail", self.view.detail_url)

    def test_titulo_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Avaliações de Documentação Médica", self.view.titulo)


class AvaliacaoMedicaDeleteViewTestCase(
    DiretorEnsinoPermissionData, UserTestMixin, TestCase
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view = views.AvaliacaoMedicaDeleteView()
        cls.grupo_sistemico = Group.objects.create(name=models.GRUPO_SISTEMICO)
        cls.usuario_base.groups.add(cls.grupo_sistemico)

    def test_changelist_name_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Documentações Médicas", self.view.changelist_name)

    def test_changelist_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual("avaliacao_medica_changelist", self.view.changelist_url)

    def test_titulo_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Excluir avaliação médica", self.view.titulo)

    def test_success_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual(reverse("avaliacao_medica_changelist"), self.view.success_url)

    def test_deveria_deletar_avaliacao(self):
        avaliacao = recipes.avaliacao.make()
        mommy.make(
            "editais.PeriodoConvocacao",
            evento=EventoCronogramaChoices.ANALISE.name,
            etapa=avaliacao.analise_documental.confirmacao_interesse.etapa,
        )
        self.client.logout()
        self.client.login(username=self.usuario_base.username, password="123")
        response = self.client.post(
            reverse("avaliacao_medica_delete", args=[avaliacao.id]),
        )
        self.assertEqual(reverse("avaliacao_medica_changelist"), response.url)


class AvaliacaoMedicaCreateViewTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view = views.AvaliacaoMedicaCreateView()

    def test_tipo_analise_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            models.TipoAnalise.TIPO_AVALIACAO_MEDICA, self.view.tipo_analise
        )

    def test_success_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual(reverse("avaliacao_medica_changelist"), self.view.success_url)

    def test_changelist_name_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Documentações Médicas", self.view.changelist_name)

    def test_changelist_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual("avaliacao_medica_changelist", self.view.changelist_url)

    def test_titulo_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Nova avaliação médica", self.view.titulo)


class AvaliacaoMedicaDetailViewTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view = views.AvaliacaoMedicaDetailView()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.avaliacao = recipes.avaliacao.make()
        cls.view.setup(cls.request, pk=cls.avaliacao.pk)

    def test_changelist_name_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Documentações Médicas", self.view.changelist_name)

    def test_changelist_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual("avaliacao_medica_changelist", self.view.changelist_url)

    def test_get_titulo_deveria_estar_corretamente_configurado(self):
        expected = f"Avaliação médica de {self.avaliacao.analise_documental.confirmacao_interesse.inscricao.candidato}"
        self.assertEqual(expected, self.view.get_titulo())


class AvaliacaoSocioeconomicaListViewTestCase(
    DiretorEnsinoPermissionData, UserTestMixin, TestCase
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view = views.AvaliacaoSocioeconomicaListView()

    def test_tipo_analise_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            models.TipoAnalise.TIPO_AVALIACAO_SOCIOECONOMICA, self.view.tipo_analise
        )

    def test_add_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual("avaliacao_socioeconomica_add", self.view.add_url)

    def test_change_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual("avaliacao_socioeconomica_update", self.view.change_url)

    def test_delete_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual("avaliacao_socioeconomica_delete", self.view.delete_url)

    def test_detail_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual("avaliacao_socioeconomica_detail", self.view.detail_url)

    def test_titulo_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Avaliações de Documentação Socioeconômica", self.view.titulo)


class AvaliacaoSocioeconomicaCreateViewTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view = views.AvaliacaoSocioeconomicaCreateView()

    def test_tipo_analise_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            models.TipoAnalise.TIPO_AVALIACAO_SOCIOECONOMICA, self.view.tipo_analise
        )

    def test_success_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            reverse("avaliacao_socioeconomica_changelist"), self.view.success_url
        )

    def test_changelist_name_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Documentações Socioeconômicas", self.view.changelist_name)

    def test_changelist_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            "avaliacao_socioeconomica_changelist", self.view.changelist_url
        )

    def test_titulo_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Nova avaliação socioeconômica", self.view.titulo)


class AvaliacaoSocioeconomicaUpdateViewTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view = views.AvaliacaoSocioeconomicaUpdateView()

    def test_tipo_analise_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            models.TipoAnalise.TIPO_AVALIACAO_SOCIOECONOMICA, self.view.tipo_analise
        )

    def test_success_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            reverse("avaliacao_socioeconomica_changelist"), self.view.success_url
        )

    def test_changelist_name_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Documentações Socioeconômicas", self.view.changelist_name)

    def test_changelist_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            "avaliacao_socioeconomica_changelist", self.view.changelist_url
        )

    def test_titulo_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Editar avaliação socioeconômica", self.view.titulo)


class AvaliacaoSocioeconomicaDeleteViewTestCase(
    DiretorEnsinoPermissionData, UserTestMixin, TestCase
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view = views.AvaliacaoSocioEconomicaDeleteView()
        cls.grupo_sistemico = Group.objects.create(name=models.GRUPO_SISTEMICO)
        cls.usuario_base.groups.add(cls.grupo_sistemico)

    def test_changelist_name_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Documentações Socioeconômicas", self.view.changelist_name)

    def test_changelist_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            "avaliacao_socioeconomica_changelist", self.view.changelist_url
        )

    def test_titulo_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Excluir avaliação socioeconômica", self.view.titulo)

    def test_success_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            reverse("avaliacao_socioeconomica_changelist"), self.view.success_url
        )

    def test_deveria_deletar_avaliacao(self):
        avaliacao = recipes.avaliacao.make()
        mommy.make(
            "editais.PeriodoConvocacao",
            evento=EventoCronogramaChoices.ANALISE.name,
            etapa=avaliacao.analise_documental.confirmacao_interesse.etapa,
        )
        self.client.logout()
        self.client.login(username=self.usuario_base.username, password="123")
        response = self.client.post(
            reverse("avaliacao_socioeconomica_delete", args=[avaliacao.id]),
        )
        self.assertEqual(reverse("avaliacao_socioeconomica_changelist"), response.url)


class AvaliacaoSocioeconomicaDetailViewTestCase(DiretorEnsinoPermissionData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view = views.AvaliacaoSocioeconomicaDetailView()
        request_factory = RequestFactory()
        cls.request = request_factory.get("/admin")
        cls.avaliacao = recipes.avaliacao.make()
        cls.view.setup(cls.request, pk=cls.avaliacao.pk)

    def test_changelist_name_deveria_estar_corretamente_configurado(self):
        self.assertEqual("Documentações Socioeconômicas", self.view.changelist_name)

    def test_changelist_url_deveria_estar_corretamente_configurado(self):
        self.assertEqual(
            "avaliacao_socioeconomica_changelist", self.view.changelist_url
        )

    def test_get_titulo_deveria_estar_corretamente_configurado(self):
        expected = f"Avaliação socioeconômica de {self.avaliacao.analise_documental.confirmacao_interesse.inscricao.candidato}"
        self.assertEqual(expected, self.view.get_titulo())
