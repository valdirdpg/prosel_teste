from django.test import TestCase

from ...templatetags import analise_tags


class SituacaoFormatTestCase(TestCase):
    def test_deve_retornar_situacao_deferida_e_html_correspondente(self):
        html = '<span class="status status-deferido">Deferida</span>'
        self.assertEqual(html, analise_tags.situacao_format("Deferida"))

    def test_deve_retornar_situacao_indeferida_e_html_correspondente(self):
        html = '<span class="status status-indeferido">Indeferida</span>'
        self.assertEqual(html, analise_tags.situacao_format("Indeferida"))


class ConcluidaFormatTestCase(TestCase):
    def test_deve_retornar_situacao_sim_e_html_correspondente(self):
        html = '<span class="status status-sim">Sim</span>'
        self.assertEqual(html, analise_tags.concluida_format("Sim"))

    def test_deve_retornar_situacao_nao_e_html_correspondente(self):
        html = '<span class="status status-nao">Não</span>'
        self.assertEqual(html, analise_tags.concluida_format("Não"))
