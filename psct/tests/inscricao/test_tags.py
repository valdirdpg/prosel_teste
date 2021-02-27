from django.test import TestCase
from .. import recipes
from ...templatetags import inscricao_tags
from cursos.tests.mixins import DiretorEnsinoPermissionData


class TitleDadosVagasTestCase(DiretorEnsinoPermissionData, TestCase):
    def test_deveria_retornar_dados_vaga(self):
        processo = recipes.processo_inscricao.make(possui_segunda_opcao=False)
        inscricao = recipes.inscricao.make(edital=processo.edital)
        self.assertEqual("Dados da vaga", inscricao_tags.title_dados_vagas(inscricao))

    def test_deveria_retornar_dados_vaga_primeira_opcao(self):
        curso = recipes.curso_psct.make()
        processo = recipes.processo_inscricao.make(possui_segunda_opcao=True)
        inscricao = recipes.inscricao.make(
            edital=processo.edital, curso_segunda_opcao=curso
        )
        self.assertEqual(
            "Dados da vaga (1ª opção)", inscricao_tags.title_dados_vagas(inscricao)
        )

    def test_deveria_retornar_dados_vaga_opcao_unica(self):
        processo = recipes.processo_inscricao.make(possui_segunda_opcao=True)
        inscricao = recipes.inscricao.make(
            edital=processo.edital, curso_segunda_opcao=None
        )
        self.assertEqual(
            "Dados da vaga (opção única *)", inscricao_tags.title_dados_vagas(inscricao)
        )
