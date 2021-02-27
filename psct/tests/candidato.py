import datetime
import os

from django.test import TestCase
from django.urls import reverse

import candidatos.permissions
import editais.tests.recipes
from base.tests.mixins import UserTestMixin
from . import mixins
from . import recipes
from .. import permissions
from ..models import Candidato


class LoginTestCase(TestCase):
    def test_acessar_pagina_login(self):
        r = self.client.get(reverse("candidato_login"), follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Acesso para Candidatos")


class CandidatoCadastroFormTestCase(mixins.CandidatoMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        os.environ["RECAPTCHA_DISABLE"] = "True"

    def setUp(self) -> None:
        super().setUp()
        self.dados = {
            "nome": "Aluno do PSCT",
            "cpf": "060.464.214-89",
            "nascimento": datetime.date(2000, 1, 1),
            "nome_responsavel": "Nome da Mãe",
            "parentesco_responsavel": "PAIS",
            "sexo": "M",
            "nacionalidade": "BRASILEIRA",
            "naturalidade": "Cidade de Nascimento",
            "naturalidade_uf": "PB",
            "logradouro": "Nome da Rua",
            "numero_endereco": 1,
            "bairro": "Nome do Bairro",
            "municipio": "Nome da cidade onde mora",
            "uf": "PB",
            "cep": "58.000-000",
            "tipo_zona_residencial": "URBANA",
            "telefone": "(32) 13213-2132",
            "email": "email@ifpb.edu.br",
            "email_confirm": "email@ifpb.edu.br",
            "password": "abcd1234",
            "password_confirm": "abcd1234",
            "declara_veracidade": True,
        }

    def test_nome_com_uma_palavra(self):
        self.dados["nome"] = "Aluno"
        response = self.client.post(reverse("dados_basicos_psct"), data=self.dados, follow=True)
        self.assertContains(response, "Forneça nome e sobrenomes.")

    def test_nome_com_mais_de_trinta_caracteres(self):
        self.dados["nome"] = "Aluno nao podeTerSobrenomeComMaisDeTrintaCaracteres"
        response = self.client.post(reverse("dados_basicos_psct"), data=self.dados, follow=True)
        self.assertContains(
            response, "Forneça nome e sobrenomes separados por espaços em branco."
        )

    def test_nome_com_caracteres_numericos(self):
        self.dados["nome"] = "Aluno nao pode ter nomeCom123456"
        response = self.client.post(reverse("dados_basicos_psct"), data=self.dados, follow=True)
        self.assertContains(response, "Forneça nome e sobrenomes contendo apenas letras.")

    def test_nao_declara_veracidade(self):
        self.dados["declara_veracidade"] = False
        response = self.client.post(reverse("dados_basicos_psct"), data=self.dados, follow=True)
        self.assertContains(response, "has-error")

    def test_formato_data_incorreto(self):
        self.dados["nascimento"] = "1/1/99"
        response = self.client.post(reverse("dados_basicos_psct"), data=self.dados, follow=True)
        self.assertContains(
            response, "A data deve ser digitada no formato DD/MM/AAAA. Exemplo: 25/12/1954."
        )

    def test_cpf_invalido(self):
        self.dados["cpf"] = "000.000.000-00"
        response = self.client.post(reverse("dados_basicos_psct"), data=self.dados, follow=True)
        self.assertContains(response, "Inválido.")
        self.assertContains(response, "mask-cpf required error")

    def test_campos_do_formulario(self):
        response = self.client.get(reverse("dados_basicos_psct"), follow=True)
        self.assertContains(response, "Novo Cadastro")
        self.assertContains(response, "Informações Básicas")
        self.assertContains(response, "Endereço")
        self.assertContains(response, "Contatos")
        self.assertContains(response, "Senha")

    def test_realizar_cadastro_com_sucesso(self):
        self.assertFalse(Candidato.objects.filter(cpf=self.dados["cpf"]).exists())
        response = self.client.post(
            reverse("dados_basicos_psct"), data=self.dados, follow=True
        )
        self.assertContains(response, "Cadastro realizado com sucesso.")
        self.assertTrue(Candidato.objects.filter(cpf=self.dados["cpf"]).exists())

    def test_candidato_cadastrado_com_permissao_no_psct(self):
        response = self.client.post(
            reverse("dados_basicos_psct"), data=self.dados, follow=True
        )
        candidato = Candidato.objects.get(cpf=self.dados["cpf"])
        self.assertTrue(candidato.user.groups.filter(name="Candidatos PSCT").exists())

    def test_cadastro_sem_dados_validos(self):
        response = self.client.post(reverse("dados_basicos_psct"), data={}, follow=True)
        self.assertNotContains(response, "Cadastro realizado com sucesso.")

    def test_atualizacao_cadastro_sem_dados_validos(self):
        self.client.login(**self.candidato.user.credentials)
        r = self.client.post(
            reverse("dados_basicos_update_psct", kwargs={"pk": self.candidato.pk}),
            data={},
            follow=True,
        )
        self.assertNotContains(r, "Cadastro realizado com sucesso.")


class CandidatoTestCase(mixins.EditalTestData, mixins.CursoTestData, TestCase):
    def setUp(self):
        super().setUp()
        self.processo_seletivo = self.edital.edicao.processo_seletivo
        self.processo_inscricao = recipes.processo_inscricao.make(
            edital=self.edital, cursos=[self.curso]
        )

    def test_pode_acessar_pagina_processo_seletivo(self):
        r = self.client.get(
            reverse("processoseletivo", kwargs={"processo_pk": self.processo_seletivo.pk})
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.processo_seletivo.sigla)
        self.assertContains(r, self.processo_seletivo.descricao)

    def test_inscricoes_abertas(self):
        inicio = datetime.date.today() - datetime.timedelta(days=1)
        fim = datetime.date.today() + datetime.timedelta(days=1)
        editais.tests.recipes.periodo_selecao.make(
            edital=self.edital, inicio=inicio, fim=fim, inscricao=True
        )
        # necessário abrir o processo de inscrição
        self.processo_inscricao.data_inicio = inicio
        self.processo_inscricao.data_encerramento = fim
        self.processo_inscricao.save()
        self.assertTrue(self.processo_inscricao.em_periodo_inscricao)

        r = self.client.get(
            reverse(
                "edicao",
                kwargs={
                    "processo_pk": self.processo_seletivo.pk,
                    "edicao_pk": self.edital.edicao.pk
                },
            )
        )
        self.assertContains(r, "estou cadastrado")


class PermissoesAcessoCandidatoTestCase(mixins.CandidatoMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client.login(**self.candidato.user.credentials)

    def test_pode_acessar_area_do_candidato(self):
        response = self.client.get(reverse("index_psct"), follow=True)
        self.assertContains(response, "Minhas Inscrições")
        self.assertContains(response, "Meus Recursos")
        self.assertContains(response, "Inscrições Abertas")

    def test_pode_ver_menu_candidato(self):
        response = self.client.get(reverse("index_psct"), follow=True)
        self.assertContains(response, 'id="menu-area_candidato"')

    def test_candidato_nao_autenticado_nao_pode_ver_menu_candidato(self):
        self.client.logout()
        response = self.client.get(reverse("index_psct"), follow=True)
        self.assertNotContains(response, 'id="menu-area_candidato"')

    def test_pode_acessar_formulario_atualizacao_candidato(self):
        # Candidato logado é automaticamente redirecionado para a página de atualização de dados.
        r = self.client.get(reverse("dados_basicos_psct"), follow=True)
        self.assertContains(r, "rea do Candidato - Dados Básicos:")


class PermissoesAcessoNaoCandidatoTestCase(UserTestMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client.login(**self.usuario_base.credentials)

    def test_nao_pode_acessar_formulario_atualizacao_candidato(self):
        # Usuário que não é candidato não tem acesso a página de dados básicos.
        response = self.client.get(reverse("dados_basicos_psct"))
        self.assertContains(response, "tentar um outro endere", status_code=403)

    def test_alerta_usuario_nao_eh_candidato(self):
        response = self.client.get(reverse("index_psct"), follow=True)
        self.assertContains(
            response, "logado no Portal com um perfil administrativo.", status_code=403
        )
        self.assertContains(response, "exclusiva para candidatos do PSCT.", status_code=403)


class CandidatoDadosBasicosRedirectViewTestCase(UserTestMixin, TestCase):
    def test_candidato_deveria_ser_redirecionado_para_app_candidatos(self):
        candidatos.permissions.Candidatos().sync()
        candidatos.permissions.Candidatos.add_user(self.usuario_base)
        self.client.login(**self.usuario_base.credentials)
        response = self.client.get(reverse("dados_basicos_redirect"))
        self.assertRedirects(
            response, reverse("dados_basicos_candidato"), fetch_redirect_response=False
        )

    def test_candidato_psct_deveria_ser_redirecionado_para_app_psct(self):
        permissions.CandidatosPSCT().sync()
        permissions.CandidatosPSCT.add_user(self.usuario_base)
        self.client.login(**self.usuario_base.credentials)
        response = self.client.get(reverse("dados_basicos_redirect"))
        self.assertRedirects(
            response, reverse("dados_basicos_psct"), fetch_redirect_response=False
        )
