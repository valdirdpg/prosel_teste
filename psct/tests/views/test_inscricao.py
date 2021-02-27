import datetime
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils.formats import localize
from freezegun import freeze_time
from model_mommy import mommy

import cursos.models
from base.configs import PortalConfig
from base.tests.mixins import UserTestMixin
from processoseletivo.models import ModalidadeEnum
from .. import mixins
from .. import recipes
from ... import models
from ... import permissions
from ...forms import inscricao as forms
from ...models import format_curso
from ...views import inscricao as views


class ProcessoInscricaoTest(UserTestMixin, mixins.EditalTestData, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.usuario_base.is_staff = True
        cls.usuario_base.is_superuser = True
        cls.usuario_base.save()

    def setUp(self):
        super().setUp()
        self.client.login(**self.usuario_base.credentials)

    def test_cadastro(self):
        date_today = datetime.date.today()
        response = self.client.post(
            reverse("admin:psct_processoinscricao_add"),
            data=dict(
                edital=self.edital.id,
                formacao="SUBSEQUENTE",
                data_inicio=localize(date_today),
                data_encerramento=localize(date_today),
            ),
        )
        self.assertEqual(response.status_code, 200)


class VagasProcessoInscricaoTestCase(
    UserTestMixin, mixins.EditalTestData, mixins.CursoTestData, TestCase
):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        permissions.AdministradoresPSCT().sync()
        cls.modalidade_ampla = models.Modalidade.objects.get(
            equivalente=ModalidadeEnum.ampla_concorrencia
        )
        cls.modalidade_cota_racial = models.Modalidade.objects.get(
            equivalente=ModalidadeEnum.cota_racial
        )
        cls.processo_inscricao = recipes.processo_inscricao.make(
            edital=cls.edital,
            cursos=[cls.curso]
        )
        cls.usuario_base.is_staff = True
        cls.usuario_base.is_active = True
        cls.usuario_base.save()

    def setUp(self):
        super().setUp()
        permissions.AdministradoresPSCT.add_user(self.usuario_base)
        self.client.login(**self.usuario_base.credentials)

    def test_adminstrador_pode_ver_botao_adicionar_vagas(self):
        url_botao_add_vagas = reverse(
            "adicionar_curso_edital_psct",
            args=[self.processo_inscricao.pk]
        )
        response = self.client.get(reverse("admin:psct_processoinscricao_changelist"))
        self.assertContains(response, url_botao_add_vagas)
        self.assertContains(response, "Adicionar vagas")

    def test_criacao_de_vagas_em_processo_seletivo(self):
        self.assertFalse(models.CursoEdital.objects.exists())
        url_add_vagas = reverse(
            "adicionar_curso_edital_psct",
            args=[self.processo_inscricao.pk]
        )
        response = self.client.post(url_add_vagas, follow=True)

        self.assertContains(response, "Adicionados curso do edital com sucesso!")
        self.assertTrue(models.CursoEdital.objects.exists())
        self.assertEquals(
            self.processo_inscricao.cursos.count(),
            models.CursoEdital.objects.count()
        )


class InscricaoCandidatoTestCase(mixins.CandidatoMixin, mixins.ProcessoInscricaoMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.client.login(**self.candidato.user.credentials)

    def test_candidato_logado(self):
        url_inscricao = reverse("base")
        response = self.client.get(url_inscricao, follow=True)
        self.assertContains(response, self.candidato.user.first_name)
        self.assertContains(response, "Bem-vindo")

    def test_exigir_atualizar_dados_candidato(self):
        # Definindo data da atualização no passado
        dias_passado = PortalConfig.DIAS_ATUALIZACAO_DADOS + 1
        data_passado = datetime.date.today() - datetime.timedelta(days=dias_passado)
        with freeze_time(data_passado.strftime("%Y-%m-%d")):
            self.candidato.save()

        url_inscricao = reverse("inscricao_edital_psct", args=[self.edital.pk])
        response = self.client.get(url_inscricao, follow=True)
        self.assertContains(response, "Primeiramente, atualize os seus dados de cadastro ")
        self.assertContains(response, "rea do Candidato - Dados B")

    def test_candidato_nao_pode_acessar_inscricao_cancelada(self):
        inscricao = recipes.inscricao.make(
            candidato=self.candidato,
            edital=self.edital,
            curso=self.curso_tecnico,
            modalidade_cota=self.modalidade_ampla
        )
        cancelamento = models.CancelamentoInscricao.objects.create(
            inscricao=inscricao,
            usuario=self.candidato.user
        )
        url_inscricao = reverse("inscricao_edital_psct", args=[self.edital.pk])
        response = self.client.get(url_inscricao, follow=True)
        self.assertContains(response, " precisa desfazer o cancelamento da inscri")

    def test_cancidato_deve_acessar_questionario_socioeconomico(self):
        url_inscricao = reverse("inscricao_edital_psct", args=[self.edital.pk])
        response_inscricao = self.client.get(url_inscricao, follow=True)
        self.assertContains(response_inscricao, "Questionário socioeconômico")

    def test_candidato_pode_acessar_formulario_de_inscricao(self):
        url_inscricao = reverse("create_inscricao_psct", args=[self.edital.pk])
        response_inscricao = self.client.get(url_inscricao, follow=True)
        self.assertContains(response_inscricao, "Nova Inscrição - Escolha de Curso")
        self.assertContains(response_inscricao, format_curso(self.curso_tecnico))

    def test_realizar_inscricao_escolher_curso(self):
        # Selecionar Curso, campus e cota
        url_inscricao = reverse("create_inscricao_psct", args=[self.edital.pk])
        total_inscricoes = models.Inscricao.objects.count()
        self.assertEquals(0, total_inscricoes)
        dados_inscricao = {
            "candidato": self.candidato.pk,
            "edital": self.edital.pk,
            "campus": self.curso_tecnico.campus.pk,
            "curso": self.curso_tecnico.pk,
            "cotista": "NAO",
        }
        response_inscricao = self.client.post(url_inscricao, data=dados_inscricao, follow=True)
        self.assertContains(response_inscricao, "Selecione como você pretende concorrer")
        self.assertContains(response_inscricao, "Marque como pretende concorrer")
        self.assertEquals(total_inscricoes + 1, models.Inscricao.objects.count())

    def test_realizar_inscricao_selecionar_tipos_de_notas(self):
        inscricao = recipes.inscricao.make(
            candidato=self.candidato,
            edital=self.edital,
            curso=self.curso_tecnico,
            modalidade_cota=self.modalidade_ampla,
            aceite=False
        )

        # Selecionar tipo de notas
        url_tipo_notas = reverse("selecionar_ensino_psct", args=[inscricao.pontuacao.pk])
        dados_tipo_notas = {"ensino": "OUTROS", }
        response = self.client.post(url_tipo_notas, data=dados_tipo_notas, follow=True)
        self.assertContains(response, "Notas da Inscrição")
        self.assertContains(response, "Português")
        self.assertContains(response, "Matemática")

    def test_realizar_inscricao_inserir_notas(self):
        inscricao = recipes.inscricao.make(
            candidato=self.candidato,
            edital=self.edital,
            curso=self.curso_tecnico,
            modalidade_cota=self.modalidade_ampla,
            aceite=False
        )
        inscricao.pontuacao.ensino_regular = False
        inscricao.pontuacao.save()
        inscricao.pontuacao.criar_notas()

        # Inserir notas
        url_informar_notas = reverse("notas_inscricao_psct", args=[inscricao.pontuacao.pk])
        dados_notas = {
            "notas-TOTAL_FORMS": "1",
            "notas-INITIAL_FORMS": "1",
            "notas-0-ano": "0",
            "notas-0-portugues": "9",
            "notas-0-matematica": "8",
            "notas-0-id": inscricao.pontuacao.notas.first().pk,
            "notas-0-pontuacao": inscricao.pontuacao.pk,
        }
        response_notas = self.client.post(url_informar_notas, data=dados_notas, follow=True)
        self.assertContains(response_notas, "Documentos comprobatórios")
        self.assertContains(response_notas, "DECLARO, para os fins de direito, sob as penas da lei")

    def test_realizar_inscricao_inserir_comprovantes(self):
        inscricao = recipes.inscricao.make(
            candidato=self.candidato,
            edital=self.edital,
            curso=self.curso_tecnico,
            modalidade_cota=self.modalidade_ampla,
            aceite=False
        )
        # Inserir Comprovantes
        url = reverse("comprovantes_inscricao_psct", args=[inscricao.pk])
        dados_comprovantes = {
            "comprovantes-TOTAL_FORMS": "1",
            "comprovantes-INITIAL_FORMS": "0",
            "comprovantes-MIN_NUM_FORMS": "1",
            "comprovantes-0-nome": "Histórico",
            "comprovantes-0-arquivo": SimpleUploadedFile('arquivo.jpg', b'meu comprovante'),
            "comprovantes-0-inscricao": inscricao.pk,
            "aceite": True,
        }
        response = self.client.post(url, data=dados_comprovantes, follow=True)
        self.assertContains(response, "Inscrição concluída com sucesso")
        self.assertContains(response, self.candidato.cpf)
        self.assertContains(response, self.curso_tecnico.curso.nome)


class CreateInscricaoTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.processo_inscricao = recipes.processo_inscricao.make()
        cls.edital = cls.processo_inscricao.edital
        cls.request = mock.Mock()
        cls.request.user = recipes.candidato.make().user
        cls.view_class = views.CreateInscricao

    def setUp(self) -> None:
        super().setUp()
        self.view = self.view_class()

    def test_get_template_names_de_cursos_tecnicos_deveria_estar_corretamente_configurado(self):
        processo_inscricao = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.SUBSEQUENTE
        )
        self.view.setup(self.request, edital_pk=processo_inscricao.edital.id)
        self.assertEqual(
            ["psct/create_inscricao.html"],
            self.view.get_template_names()
        )

    def test_get_template_names_de_cursos_superiores_com_uma_opcao_de_curso(self):
        processo_inscricao = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.GRADUACAO,
            possui_segunda_opcao=False,
        )
        self.view.setup(self.request, edital_pk=processo_inscricao.edital.id)
        self.assertEqual(
            ["psct/inscricao/create_inscricao_graduacao.html"],
            self.view.get_template_names()
        )

    def test_get_template_names_de_cursos_superiores_com_duas_opcoes_de_curso(self):
        processo_inscricao = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.GRADUACAO,
            possui_segunda_opcao=True,
        )
        self.view.setup(self.request, edital_pk=processo_inscricao.edital.id)
        self.assertEqual(
            ["psct/inscricao/create_inscricao_graduacao_segunda_opcao.html"],
            self.view.get_template_names()
        )

    def test_get_form_class_de_cursos_tecnicos_deveria_estar_corretamente_configurado(self):
        processo_inscricao = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.SUBSEQUENTE
        )
        self.view.setup(self.request, edital_pk=processo_inscricao.edital.id)
        self.assertEqual(forms.InscricaoForm, self.view.get_form_class())

    def test_get_form_class_de_cursos_superiores_com_uma_opcao_de_curso(self):
        processo_inscricao = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.GRADUACAO,
            possui_segunda_opcao=False,
        )
        self.view.setup(self.request, edital_pk=processo_inscricao.edital.id)
        self.assertEqual(forms.InscricaoGraduacaoForm, self.view.get_form_class())

    def test_get_form_class_de_cursos_superiores_com_duas_opcoes_de_curso(self):
        processo_inscricao = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.GRADUACAO,
            possui_segunda_opcao=True,
        )
        self.view.setup(self.request, edital_pk=processo_inscricao.edital.id)
        self.assertEqual(forms.InscricaoSegundaOpcaoGraduacaoForm, self.view.get_form_class())

    def test_template_name_deve_estar_corretamente_configurado(self):
        self.assertEqual(
            "psct/create_inscricao.html",
            self.view.template_name
        )

    def test_form_class_deve_estar_corretamente_configurado(self):
        self.assertEqual(forms.InscricaoForm, self.view.form_class)

    def test_usuario_anonimo_deveria_ser_redirecionado_ao_login(self):
        processo_inscricao = recipes.processo_inscricao.make()
        response = self.client.get(
            reverse("create_inscricao_psct", args=[processo_inscricao.edital.pk])
        )
        self.assertEqual(
            f"/login/?next=/psct/inscricao/add/{processo_inscricao.edital.pk}/",
            response.url
        )


class UpdateInscricaoTestCase(TestCase):
    campus_patcher: mock.patch.multiple

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.processo_inscricao = recipes.processo_inscricao.make()
        cls.edital = cls.processo_inscricao.edital
        cls.campus_patcher = mock.patch.multiple(
            cursos.models.Campus,
            cria_usuarios_diretores=mock.DEFAULT,
            adiciona_permissao_diretores=mock.DEFAULT,
            remove_permissao_diretores=mock.DEFAULT,
        )
        cls.campus_patcher.start()
        cls.inscricao = recipes.inscricao.make(edital=cls.edital)
        cls.request = mock.Mock()
        cls.request.user = recipes.candidato.make().user
        cls.view_class = views.UpdateInscricao

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.campus_patcher.stop()

    def setUp(self) -> None:
        super().setUp()
        self.view = self.view_class()

    def test_get_template_names_de_cursos_tecnicos_deveria_estar_corretamente_configurado(self):
        processo_inscricao = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.SUBSEQUENTE
        )
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.view.setup(self.request, pk=inscricao.id)
        self.assertEqual(
            ["psct/create_inscricao.html"],
            self.view.get_template_names()
        )

    def test_get_template_names_de_cursos_superiores_com_uma_opcao_de_curso(self):
        processo_inscricao = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.GRADUACAO,
            possui_segunda_opcao=False,
        )
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.view.setup(self.request, pk=inscricao.id)
        self.assertEqual(
            ["psct/inscricao/create_inscricao_graduacao.html"],
            self.view.get_template_names()
        )

    def test_get_template_names_de_cursos_superiores_com_duas_opcoes_de_curso(self):
        processo_inscricao = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.GRADUACAO,
            possui_segunda_opcao=True,
        )
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.view.setup(self.request, pk=inscricao.id)
        self.assertEqual(
            ["psct/inscricao/create_inscricao_graduacao_segunda_opcao.html"],
            self.view.get_template_names()
        )

    def test_get_form_class_de_cursos_tecnicos_deveria_estar_corretamente_configurado(self):
        processo_inscricao = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.SUBSEQUENTE
        )
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.view.setup(self.request, pk=inscricao.id)
        self.assertEqual(forms.InscricaoForm, self.view.get_form_class())

    def test_get_form_class_de_cursos_superiores_com_uma_opcao_de_curso(self):
        processo_inscricao = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.GRADUACAO,
            possui_segunda_opcao=False,
        )
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.view.setup(self.request, pk=inscricao.id)
        self.assertEqual(forms.InscricaoGraduacaoForm, self.view.get_form_class())

    def test_get_form_class_de_cursos_superiores_com_duas_opcoes_de_curso(self):
        processo_inscricao = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.GRADUACAO,
            possui_segunda_opcao=True,
        )
        inscricao = recipes.inscricao.make(edital=processo_inscricao.edital)
        self.view.setup(self.request, pk=inscricao.id)
        self.assertEqual(forms.InscricaoSegundaOpcaoGraduacaoForm, self.view.get_form_class())

    def test_template_name_deve_estar_corretamente_configurado(self):
        self.assertEqual(
            "psct/create_inscricao.html",
            self.view.template_name
        )

    def test_form_class_deve_estar_corretamente_configurado(self):
        self.assertEqual(forms.InscricaoForm, self.view.form_class)


class ModalidadeTestCase(TestCase):
    fixtures = ["modalidade.json"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.processo_inscricao_tecnico = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.INTEGRADO
        )
        cls.processo_inscricao_superior = recipes.processo_inscricao.make(
            formacao=models.ProcessoInscricao.GRADUACAO
        )

    def test_deveria_retornar_ensino_medio_em_cota_escola_pulica_formacao_superior(
            self,
    ):
        modalidade = mommy.make(
            models.Modalidade,
            texto="ENSINO FUNDAMENTAL",
            equivalente_id=ModalidadeEnum.escola_publica,
        )
        self.assertEqual(
            "ENSINO MÉDIO",
            modalidade.por_nivel_formacao(self.processo_inscricao_superior),
        )

    def test_deveria_retornar_ensino_fundamental_em_cota_escola_publica_com_formacao_tecnica(
            self,
    ):
        modalidade = mommy.make(
            models.Modalidade,
            texto="ENSINO FUNDAMENTAL",
            equivalente_id=ModalidadeEnum.escola_publica,
        )
        self.assertEqual(
            "ENSINO FUNDAMENTAL",
            modalidade.por_nivel_formacao(self.processo_inscricao_tecnico),
        )

    def test_deveria_retornar_campi_picui_e_sousa_em_cota_rural_com_formacao_superior(
            self,
    ):
        modalidade = mommy.make(
            models.Modalidade,
            texto="IFPB - CAMPUS SOUSA",
            equivalente_id=ModalidadeEnum.rurais,
        )
        self.assertIn(
            "IFPB NOS CAMPI PICUÍ E SOUSA",
            modalidade.por_nivel_formacao(self.processo_inscricao_superior),
        )

    def test_nao_deveria_retornar_campi_picui_em_cota_rural_com_formacao_tecnica(self):
        modalidade = mommy.make(
            models.Modalidade,
            texto="IFPB - CAMPUS SOUSA",
            equivalente_id=ModalidadeEnum.rurais,
        )
        self.assertNotIn(
            "IFPB NOS CAMPI PICUÍ E SOUSA",
            modalidade.por_nivel_formacao(self.processo_inscricao_tecnico),
        )
