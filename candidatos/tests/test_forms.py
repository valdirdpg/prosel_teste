from datetime import date

from django.test import TestCase
from model_mommy import mommy

from candidatos import forms


class CandidatoPreMatriculaFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.titulo_fields = [
            "numero_titulo_eleitor",
            "uf_titulo_eleitor",
            "secao_titulo_eleitor",
            "zona_titulo_eleitor",
            "data_emissao_titulo_eleitor",
        ]
        cls.data = dict(
            uf_titulo_eleitor="PB",
            zona_titulo_eleitor="13",
            secao_titulo_eleitor="123",
            numero_titulo_eleitor="111111111309",
            data_emissao_titulo_eleitor=date.today().strftime("%Y-%m-%d"),
        )
        cls.pessoa = mommy.make(
            "base.PessoaFisica",
            nome="usuario teste",
            uf_titulo_eleitor="PB",
            zona_titulo_eleitor="13",
            secao_titulo_eleitor="123",
            numero_titulo_eleitor="111111111309",
            data_emissao_titulo_eleitor=date.today().strftime("%Y-%m-%d"),
            _fill_optional=True,
        )

    def get_clean_data(self):
        data = {}
        for field in self.titulo_fields:
            data[field] = ""
        return data

    def test_titulo_eleitor_vazio_nao_valida(self):
        data = self.get_clean_data()
        form = forms.CandidatoPreMatriculaForm(data)
        form.is_valid()
        for field in self.titulo_fields:
            self.assertFalse(form[field].errors)