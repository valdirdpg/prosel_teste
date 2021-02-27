from django.test import TestCase

import base.tests.recipes
from cursos.permissions import DiretoresdeEnsino
from .. import recipes
from ... import permissions, models
from ...forms import analise as forms


class AvaliarInscricaoAvaliadorFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        DiretoresdeEnsino().sync()
        permissions.AvaliadorPSCT().sync()
        cls.field_names = ["inscricao", "situacao", "texto_indeferimento", "avaliador", "concluida"]
        cls.inscricao = recipes.inscricao_pre_analise.make()
        cls.avaliador = base.tests.recipes.user.make()

    def setUp(self):
        super().setUp()
        self.form = forms.AvaliarInscricaoAvaliadorForm(self.inscricao, data={})
        self.data = {
            "inscricao": self.inscricao.pk,
            "avaliador": self.avaliador.pk,
            "concluida": models.Concluida.NAO.name
        }

    def test_deveria_exibir_todos_os_campos(self):
        self.assertListEqual(sorted(self.form.fields.keys()), sorted(self.field_names))

    def test_campo_inscricao_deveria_estar_oculto(self):
        self.assertIn(self.form["inscricao"], self.form.hidden_fields())

    def test_campo_avaliador_deveria_estar_oculto(self):
        self.assertIn(self.form["avaliador"], self.form.hidden_fields())

    def test_deveria_validar_se_ha_justificativa_quando_avaliacao_eh_indeferida(self):
        self.data.update(
            situacao=models.SituacaoAvaliacao.INDEFERIDA.name,
            texto_indeferimento=None,
        )
        form = forms.AvaliarInscricaoAvaliadorForm(self.inscricao, data=self.data)
        form.is_valid()
        self.assertIn(
            "Você precisa justificar o indeferimento",
            form.errors["texto_indeferimento"],
        )

    def test_deveria_validar_se_nao_ha_justificativa_quando_avaliacao_eh_deferida(self):
        texto_indeferimento = recipes.justificativa_indeferimento.make(
            edital=self.inscricao.fase.edital
        )
        self.data.update(
            situacao=models.SituacaoAvaliacao.DEFERIDA.name,
            texto_indeferimento=texto_indeferimento.pk,
        )
        form = forms.AvaliarInscricaoAvaliadorForm(self.inscricao, data=self.data)
        form.is_valid()
        self.assertIn(
            "Inscrição deferida não requer justificativa",
            form.errors["texto_indeferimento"],
        )

    def test_formulario_deveria_ser_valido(self):
        data = {
            "inscricao": self.inscricao.pk,
            "situacao": models.SituacaoAvaliacao.DEFERIDA.name,
            "avaliador": self.avaliador.pk,
            "concluida": models.Concluida.NAO.name
        }
        form = forms.AvaliarInscricaoAvaliadorForm(self.inscricao, data=data)
        self.assertTrue(form.is_valid())


class AvaliacaoAvaliadorAdminFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        DiretoresdeEnsino().sync()
        permissions.AvaliadorPSCT().sync()
        cls.field_names = ["concluida"]

    def setUp(self):
        super().setUp()
        self.form = forms.AvaliacaoAvaliadorAdminForm(data={})

    def test_deveria_exibir_todos_os_campos(self):
        self.assertListEqual(sorted(self.form.fields.keys()), sorted(self.field_names))

    def test_deveria_validar_se_ha_avaliacao_registrada_para_a_inscricao(self):
        avaliacao_homologador = recipes.avaliacao_homologador.make()
        avaliacao_avaliador = recipes.avaliacao_avaliador.make(
            inscricao=avaliacao_homologador.inscricao
        )
        form = forms.AvaliacaoAvaliadorAdminForm(data={}, instance=avaliacao_avaliador)
        form.is_valid()
        self.assertIn(
            "Você não pode alterar a avaliação pois o homologador já avaliou a inscrição",
            form.non_field_errors(),
        )

    def test_formulario_deveria_ser_valido(self):
        avaliacao_avaliador = recipes.avaliacao_avaliador.make()
        data = {"concluida": avaliacao_avaliador.concluida}
        form = forms.AvaliacaoAvaliadorAdminForm(data=data, instance=avaliacao_avaliador)
        self.assertTrue(form.is_valid())
