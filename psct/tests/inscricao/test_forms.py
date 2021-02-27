from unittest import mock

from django.test import TestCase

import cursos.models
import cursos.recipes
import editais.tests.recipes
from processoseletivo.models import ModalidadeEnum
from psct.forms import inscricao as forms
from .. import recipes
from ...models import Modalidade


class CursoEditalFormTestCase(TestCase):

    def test_todos_os_fields_deveriam_estar_corretamente_configurados(self):
        form = forms.CursoEditalForm()
        self.assertEqual(
            ("edital", "curso"),
            tuple(form.fields.keys())
        )

    def test_campo_edital_deve_ter_editais_com_processos_inscricao_cadastrados(self):
        processo_inscricao = recipes.processo_inscricao.make()
        form = forms.CursoEditalForm()
        self.assertIn(processo_inscricao.edital, form.fields["edital"].queryset)

    def test_campo_edital_nao_deve_ter_editais_sem_processos_inscricao_cadastrados(self):
        edital = editais.tests.recipes.edital.make()
        form = forms.CursoEditalForm()
        self.assertNotIn(edital, form.fields["edital"].queryset)

    def test_campo_curso_deve_ter_cursos_associados_a_processos_inscricao(self):
        with mock.patch.multiple(
                cursos.models.Campus,
                cria_usuarios_diretores=mock.DEFAULT,
                adiciona_permissao_diretores=mock.DEFAULT,
                remove_permissao_diretores=mock.DEFAULT,
        ):
            curso = cursos.recipes.curso_selecao.make()
        recipes.processo_inscricao.make(
            cursos=[curso]
        )
        form = forms.CursoEditalForm()
        self.assertIn(curso, form.fields["curso"].queryset)

    def test_campo_curso_nao_deve_ter_cursos_sem_processos_inscricao(self):
        with mock.patch.multiple(
                cursos.models.Campus,
                cria_usuarios_diretores=mock.DEFAULT,
                adiciona_permissao_diretores=mock.DEFAULT,
                remove_permissao_diretores=mock.DEFAULT,
        ):
            curso = cursos.recipes.curso_selecao.make()
        form = forms.CursoEditalForm()
        self.assertNotIn(curso, form.fields["curso"].queryset)


class InscricaoGraduacaoFormTestCase(TestCase):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]
    campus_patcher: mock.patch.multiple
    form_class = forms.InscricaoGraduacaoForm

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.campus_patcher = mock.patch.multiple(
            cursos.models.Campus,
            cria_usuarios_diretores=mock.DEFAULT,
            adiciona_permissao_diretores=mock.DEFAULT,
            remove_permissao_diretores=mock.DEFAULT,
        )
        cls.campus_patcher.start()

    def setUp(self) -> None:
        super().setUp()
        self.processo_inscricao = recipes.processo_inscricao.make(possui_segunda_opcao=False)
        self.curso = cursos.recipes.curso_selecao_graduacao.make()
        self.processo_inscricao.cursos.add(
            self.curso
        )
        self.form = forms.InscricaoGraduacaoForm(
            initial={
                "candidato": recipes.candidato.make(),
                "edital": self.processo_inscricao.edital,
            }
        )

    def test_campo_curso_deve_ter_label_configurado_corretamente(self):
        self.assertEqual(
            "Primeira opção de curso",
            self.form.fields["curso"].label
        )

    def test_campo_aceite_deve_ser_obrigatorio(self):
        self.assertTrue(self.form.fields["aceite"].required)

    def test_campo_aceite_deve_ser_inicialmente_nao_selecionado(self):
        self.assertFalse(self.form.fields["aceite"].initial)

    def test_campo_aceite_nao_deve_ter_estilo_css_no_widget(self):
        self.assertNotIn("class", self.form.fields["aceite"].widget.attrs)

    def test_campo_cotista_nao_deve_ter_estilo_css_no_widget(self):
        self.assertNotIn("class", self.form.fields["cotista"].widget.attrs)

    def test_campo_modalidade_cota_nao_deve_ter_estilo_css_no_widget(self):
        self.assertNotIn("class", self.form.fields["modalidade_cota"].widget.attrs)

    def test_campo_curso_deve_ter_estilo_css_no_widget(self):
        self.assertIn("form-control", self.form.fields["curso"].widget.attrs["class"])

    def test_campo_candidato_deve_ter_widget_hidden(self):
        self.assertIn(self.form["candidato"], self.form.hidden_fields())

    def test_campo_edital_deve_ter_widget_hidden(self):
        self.assertIn(self.form["edital"], self.form.hidden_fields())

    def test_campo_curso_deveria_listar_cursos_do_processo_inscricao(self):
        self.assertIn(self.curso, self.form.fields["curso"].queryset)

    def test_campo_curso_deveria_listar_cursos_a_partir_do_instance(self):
        inscricao = recipes.inscricao.make(
            edital=self.processo_inscricao.edital,
            curso=self.curso
        )
        form = self.form_class(
            initial={"candidato": recipes.candidato.make()},
            instance=inscricao,
        )
        self.assertIn(self.curso, form.fields["curso"].queryset)

    def test_campo_curso_nao_deveria_listar_cursos_fora_do_processo_inscricao(self):
        curso_fora = cursos.recipes.curso_selecao_graduacao.make()
        self.assertNotIn(curso_fora, self.form.fields["curso"].queryset)

    def test_campo_cotista_deveria_marcar_nao_se_candidato_inscricao_eh_ampla(self):
        ampla = Modalidade.objects.get(equivalente_id=ModalidadeEnum.ampla_concorrencia)
        candidato = recipes.candidato.make()
        inscricao = recipes.inscricao.make(
            candidato=candidato,
            edital=self.processo_inscricao.edital,
            modalidade_cota=ampla
        )
        form = self.form_class(
            initial={
                "candidato": candidato,
                "edital": self.processo_inscricao.edital,
            },
            instance=inscricao,
        )
        self.assertEqual("NAO", form.fields["cotista"].initial)

    def test_campo_cotista_deveria_marcar_sim_se_candidato_inscricao_nao_eh_ampla(self):
        nao_ampla = Modalidade.objects.get(equivalente_id=ModalidadeEnum.escola_publica)
        candidato = recipes.candidato.make()
        inscricao = recipes.inscricao.make(
            candidato=candidato,
            edital=self.processo_inscricao.edital,
            modalidade_cota=nao_ampla
        )
        form = self.form_class(
            initial={
                "candidato": candidato,
                "edital": self.processo_inscricao.edital,
            },
            instance=inscricao,
        )
        self.assertEqual("SIM", form.fields["cotista"].initial)

    def test_deveria_validar_campo_modalidade_cota_se_cota_nao_for_selecionada(self):
        candidato =  recipes.candidato.make()
        form = self.form_class(
            data={
                "candidato": candidato.id,
                "edital": self.processo_inscricao.edital.id,
                "cotista": "SIM",
            },
            initial={
                "candidato": candidato,
                "edital": self.processo_inscricao.edital,
            },
        )
        form.is_valid()
        self.assertIn(
            "Você deve selecionar a modalidade da cota que gostaria concorrer ou "
            "marcar a opção de não concorrer por cota.",
            form.errors["modalidade_cota"],
        )

    def test_deveria_selecionar_ampla_automaticamente_se_nao_optou_por_cotas(self):
        candidato = recipes.candidato.make()
        form = self.form_class(
            data={
                "candidato": candidato.id,
                "edital": self.processo_inscricao.edital.id,
                "cotista": "NAO",
            },
            initial={
                "candidato": candidato,
                "edital": self.processo_inscricao.edital,
            },
        )
        ampla = Modalidade.objects.get(equivalente_id=ModalidadeEnum.ampla_concorrencia)
        form.is_valid()
        self.assertEqual(ampla, form.cleaned_data["modalidade_cota"])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.campus_patcher.stop()


class InscricaoSegundaOpcaoGraduacaoFormTestCase(TestCase):
    fixtures = [
        "processoseletivo/fixtures/modalidade.json",
        "psct/tests/fixtures/modalidade_cota.json",
    ]
    campus_patcher: mock.patch.multiple
    form_class = forms.InscricaoSegundaOpcaoGraduacaoForm
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.campus_patcher = mock.patch.multiple(
            cursos.models.Campus,
            cria_usuarios_diretores=mock.DEFAULT,
            adiciona_permissao_diretores=mock.DEFAULT,
            remove_permissao_diretores=mock.DEFAULT,
        )
        cls.campus_patcher.start()

    def setUp(self) -> None:
        super().setUp()
        self.processo_inscricao = recipes.processo_inscricao.make(possui_segunda_opcao=True)
        self.curso = cursos.recipes.curso_selecao_graduacao.make()
        self.processo_inscricao.cursos.add(
            self.curso
        )
        self.form = self.form_class(
            initial={
                "candidato": recipes.candidato.make(),
                "edital": self.processo_inscricao.edital,
            }
        )

    def test_campo_curso_deve_ter_label_configurado_corretamente(self):
        self.assertEqual(
            "Primeira opção de curso",
            self.form.fields["curso"].label
        )

    def test_campo_curso_segunda_opcao_deve_ter_label_configurado_corretamente(self):
        self.assertEqual(
            "Segunda opção de curso",
            self.form.fields["curso_segunda_opcao"].label
        )

    def test_campo_aceite_deve_ser_obrigatorio(self):
        self.assertTrue(self.form.fields["aceite"].required)

    def test_campo_aceite_deve_ser_inicialmente_nao_selecionado(self):
        self.assertFalse(self.form.fields["aceite"].initial)

    def test_campo_aceite_nao_deve_ter_estilo_css_no_widget(self):
        self.assertNotIn("class", self.form.fields["aceite"].widget.attrs)

    def test_campo_cotista_nao_deve_ter_estilo_css_no_widget(self):
        self.assertNotIn("class", self.form.fields["cotista"].widget.attrs)

    def test_campo_modalidade_cota_nao_deve_ter_estilo_css_no_widget(self):
        self.assertNotIn("class", self.form.fields["modalidade_cota"].widget.attrs)

    def test_campo_com_segunda_opcao_nao_deve_ter_estilo_css_no_widget(self):
        self.assertNotIn("class", self.form.fields["com_segunda_opcao"].widget.attrs)

    def test_campo_curso_deve_ter_estilo_css_no_widget(self):
        self.assertIn("form-control", self.form.fields["curso"].widget.attrs["class"])

    def test_campo_curso_segunda_opcao_deve_ter_estilo_css_no_widget(self):
        self.assertIn("form-control", self.form.fields["curso_segunda_opcao"].widget.attrs["class"])

    def test_campo_candidato_deve_ter_widget_hidden(self):
        self.assertIn(self.form["candidato"], self.form.hidden_fields())

    def test_campo_edital_deve_ter_widget_hidden(self):
        self.assertIn(self.form["edital"], self.form.hidden_fields())

    def test_campo_curso_deveria_listar_cursos_do_processo_inscricao(self):
        self.assertIn(self.curso, self.form.fields["curso"].queryset)

    def test_campo_curso_deveria_listar_cursos_a_partir_do_instance(self):
        inscricao = recipes.inscricao.make(
            edital=self.processo_inscricao.edital,
            curso=self.curso
        )
        form = self.form_class(
            initial={"candidato": recipes.candidato.make()},
            instance=inscricao,
        )
        self.assertIn(self.curso, form.fields["curso"].queryset)

    def test_campo_curso_nao_deveria_listar_cursos_sem_edital(self):
        form = self.form_class(
            initial={
                "candidato": recipes.candidato.make(),
                "edital": recipes.processo_inscricao.make().edital
            },
        )
        self.assertFalse(form.fields["curso"].queryset.exists())

    def test_campo_curso_nao_deveria_listar_cursos_fora_do_processo_inscricao(self):
        curso_fora = cursos.recipes.curso_selecao_graduacao.make()
        self.assertNotIn(curso_fora, self.form.fields["curso"].queryset)

    def test_campo_curso_segunda_opcao_deveria_listar_cursos_do_processo_inscricao(self):
        self.assertIn(self.curso, self.form.fields["curso_segunda_opcao"].queryset)

    def test_campo_curso_segunda_opcao_nao_deveria_listar_cursos_fora_do_processo_inscricao(self):
        curso_fora = cursos.recipes.curso_selecao_graduacao.make()
        self.assertNotIn(curso_fora, self.form.fields["curso_segunda_opcao"].queryset)

    def test_campo_cotista_deveria_marcar_nao_se_candidato_inscricao_eh_ampla(self):
        ampla = Modalidade.objects.get(equivalente_id=ModalidadeEnum.ampla_concorrencia)
        candidato = recipes.candidato.make()
        inscricao = recipes.inscricao.make(
            candidato=candidato,
            edital=self.processo_inscricao.edital,
            modalidade_cota=ampla
        )
        form = self.form_class(
            initial={
                "candidato": candidato,
                "edital": self.processo_inscricao.edital,
            },
            instance=inscricao,
        )
        self.assertEqual("NAO", form.fields["cotista"].initial)

    def test_campo_cotista_deveria_marcar_sim_se_candidato_inscricao_nao_eh_ampla(self):
        nao_ampla = Modalidade.objects.get(equivalente_id=ModalidadeEnum.escola_publica)
        candidato = recipes.candidato.make()
        inscricao = recipes.inscricao.make(
            candidato=candidato,
            edital=self.processo_inscricao.edital,
            modalidade_cota=nao_ampla
        )
        form = self.form_class(
            initial={
                "candidato": candidato,
                "edital": self.processo_inscricao.edital,
            },
            instance=inscricao,
        )
        self.assertEqual("SIM", form.fields["cotista"].initial)

    def test_deveria_validar_campo_modalidade_cota_se_cota_nao_for_selecionada(self):
        candidato =  recipes.candidato.make()
        form = self.form_class(
            data={
                "candidato": candidato.id,
                "edital": self.processo_inscricao.edital.id,
                "cotista": "SIM",
            },
            initial={
                "candidato": candidato,
                "edital": self.processo_inscricao.edital,
            },
        )
        form.is_valid()
        self.assertIn(
            "Você deve selecionar a modalidade da cota que gostaria concorrer ou "
            "marcar a opção de não concorrer por cota.",
            form.errors["modalidade_cota"],
        )

    def test_deveria_selecionar_ampla_automaticamente_se_nao_optou_por_cotas(self):
        candidato = recipes.candidato.make()
        form = self.form_class(
            data={
                "candidato": candidato.id,
                "edital": self.processo_inscricao.edital.id,
                "cotista": "NAO",
            },
            initial={
                "candidato": candidato,
                "edital": self.processo_inscricao.edital,
            },
        )
        ampla = Modalidade.objects.get(equivalente_id=ModalidadeEnum.ampla_concorrencia)
        form.is_valid()
        self.assertEqual(ampla, form.cleaned_data["modalidade_cota"])

    def test_deveria_validar_segunda_opcao_se_candidato_optou_por_ela(self):
        candidato = recipes.candidato.make()
        form = self.form_class(
            data={
                "candidato": candidato.id,
                "edital": self.processo_inscricao.edital.id,
                "com_segunda_opcao": "True",
            },
            initial={
                "candidato": candidato,
                "edital": self.processo_inscricao.edital,
            },
        )
        form.is_valid()
        self.assertIn(
            "Este campo é obrigatório porque você "
            "optou por ter uma segunda opção de curso.",
            form.errors["curso_segunda_opcao"],
        )

    def test_nao_deveria_ter_segunda_opcao_se_candidato_nao_optou_por_ela(self):
        outro_curso = cursos.recipes.curso_selecao_graduacao.make()
        self.processo_inscricao.cursos.add(
            outro_curso
        )
        candidato = recipes.candidato.make()
        form = self.form_class(
            data={
                "candidato": candidato.id,
                "edital": self.processo_inscricao.edital.id,
                "com_segunda_opcao": "False",
                "curso_segunda_opcao": outro_curso.id,
            },
            initial={
                "candidato": candidato,
                "edital": self.processo_inscricao.edital,
            },
        )
        form.is_valid()
        self.assertNotIn("curso_segunda_opcao", form.cleaned_data)

    def test_deveria_validar_se_curso_e_curso_segunda_opcao_forem_iguais(self):
        candidato = recipes.candidato.make()
        form = self.form_class(
            data={
                "candidato": candidato.id,
                "edital": self.processo_inscricao.edital.id,
                "com_segunda_opcao": "True",
                "curso": self.curso.id,
                "curso_segunda_opcao": self.curso.id,
            },
            initial={
                "candidato": candidato,
                "edital": self.processo_inscricao.edital,
            },
        )
        form.is_valid()
        self.assertIn(
            "A segunda opção de curso deve ser diferente da primeira opção.",
            form.errors["curso_segunda_opcao"],
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.campus_patcher.stop()
