from django.shortcuts import reverse
from django.test import TestCase

from . import recipes
from .. import tasks


class EncerramentoEtapaTaskTestCase(TestCase):
    def test_deveria_encerrar_etapa(self):
        etapa = recipes.etapa.make()
        encerramento = tasks.encerrar_etapa.apply(kwargs={}, args=[etapa.id])
        self.assertEqual(
            reverse("admin:processoseletivo_etapa_change", args=[etapa.id]),
            encerramento.info["url"],
        )
        self.assertEqual(
            "A etapa foi encerrada com sucesso!", encerramento.info["message"]
        )


class ReaberturaEtapaTaskTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.etapa = recipes.etapa.make(encerrada=True)
        cls.url = reverse("admin:processoseletivo_etapa_change", args=[cls.etapa.id])

    def test_deveria_reabrir_etapa(self):
        reabertura = tasks.reabrir_etapa.apply(kwargs={}, args=[self.etapa.id])
        self.assertEqual(self.url, reabertura.info["url"])
        self.assertEqual(
            "A etapa foi reaberta com sucesso!", reabertura.info["message"]
        )

    def test_nao_deveria_reabrir_etapa_ainda_nao_encerrada(self):
        etapa = recipes.etapa.make()
        reabertura = tasks.reabrir_etapa.apply(kwargs={}, args=[etapa.id])
        self.assertEqual(
            reverse("admin:processoseletivo_etapa_change", args=[etapa.id]),
            reabertura.info["url"],
        )
        self.assertEqual(
            "A etapa não pode ser reaberta, pois existe outra etapa posterior ou a mesma não está encerrada.",
            reabertura.info["message"],
        )

    def test_nao_deveria_reabrir_etapa_quando_existir_etapa_posterior(self):
        recipes.etapa.make(edicao=self.etapa.edicao)
        reabertura = tasks.reabrir_etapa.apply(kwargs={}, args=[self.etapa.id])
        self.assertEqual(
            reverse("admin:processoseletivo_etapa_change", args=[self.etapa.id]),
            reabertura.info["url"],
        )
        self.assertEqual(
            "A etapa não pode ser reaberta, pois existe outra etapa posterior ou a mesma não está encerrada.",
            reabertura.info["message"],
        )
