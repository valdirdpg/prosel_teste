from django.test import TestCase

from .. import forms
from .. import choices
from . import recipes


class EditalFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.field_names = {
            "inscricao_inicio",
            "inscricao_fim",
            "nome",
            "numero",
            "ano",
            "data_publicacao",
            "edicao",
            "encerrado",
            "publicado",
            "descricao",
            "prazo_pagamento",
            "link_inscricoes",
            "setor_responsavel",
            "tipo",
            "retificado",
            "palavra_chave",
            "url_video_descricao",
        }

    def setUp(self):
        super().setUp()
        self.form = forms.EditalForm(data={})

    def test_deveria_ter_a_quantidade_de_campos_esperada(self):
        self.assertCountEqual(self.form.fields.keys(), self.field_names)

    def test_deveria_exibir_todos_os_campos(self):
        self.assertListEqual(sorted(self.form.fields.keys()), sorted(self.field_names))

    def test_campo_tipo_deveria_estar_oculto(self):
        self.assertIn(self.form["tipo"], self.form.hidden_fields())

    def test_form_de_cadastro_deve_ter_tipo_como_abertura_por_padrao(self):
        self.assertEqual(choices.EditalChoices.ABERTURA.name, self.form.initial["tipo"])

    def test_form_de_edicao_deve_preencher_o_inicio_do_periodo_inscricao(self):
        periodo = recipes.periodo_selecao.make(inscricao=True)
        form = forms.EditalForm(data={}, instance=periodo.edital)
        self.assertEqual(periodo.inicio, form.initial["inscricao_inicio"])

    def test_form_de_edicao_deve_preencher_o_fim_do_periodo_inscricao(self):
        periodo = recipes.periodo_selecao.make(inscricao=True)
        form = forms.EditalForm(data={}, instance=periodo.edital)
        self.assertEqual(periodo.fim, form.initial["inscricao_fim"])

    def test_deveria_validar_se_ha_numero_ano_setor_igual_ja_cadastrado(self):
        edital = recipes.edital.make()
        data = {
            "numero": edital.numero,
            "ano": edital.ano,
            "setor_responsavel": edital.setor_responsavel,
        }
        form = forms.EditalForm(data=data)
        form.is_valid()
        self.assertIn(
            "Já existe um edital cadastrado com o mesmo número e ano pertencente a este setor.",
            form.non_field_errors(),
        )

    def test_formulario_deveria_ser_valido(self):
        periodo = recipes.periodo_selecao.make(inscricao=True)
        edital = periodo.edital
        data = {
            "numero": edital.numero,
            "ano": edital.ano,
            "setor_responsavel": edital.setor_responsavel,
            "inscricao_inicio": periodo.inicio,
            "inscricao_fim": periodo.fim,
            "nome": edital.nome,
            "edicao": edital.edicao_id,
            "descricao": edital.descricao,
            "prazo_pagamento": edital.prazo_pagamento,
            "tipo": edital.tipo,
            "data_publicacao": edital.data_publicacao,
            "palavra_chave": edital.palavra_chave_id,
        }
        form = forms.EditalForm(data=data, instance=edital)
        self.assertTrue(form.is_valid())
