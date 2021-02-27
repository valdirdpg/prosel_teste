from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from model_mommy import mommy

from base.models import PessoaFisica


class CursoDetailTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        mommy.make("auth.Group", name="Diretores de Ensino")
        mommy.make("noticias.PalavrasChave")

        cls.curso = mommy.make("cursos.CursoNoCampus", make_m2m=True)
        for periodo in range(1, 7):
            mommy.make(
                "cursos.DisciplinaCurso",
                curso=cls.curso,
                periodo=periodo,
                make_m2m=True,
            )

    def test_exibe_periodos_ordenados(self):
        r = self.client.get(reverse("curso", kwargs={"pk": self.curso.pk}))
        self.assertContains(r, self.curso.curso.nome)
        periodos_ordenados = [i for i in range(1, 7)]
        r_periodos = list(r.context_data["disciplinas"].keys())
        self.assertEqual(periodos_ordenados, r_periodos)


class CursoUpdateTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command("sync_permissions")
        mommy.make("noticias.PalavrasChave")

        cls.curso = mommy.make(
            "cursos.CursoNoCampus",
            formacao="BACHARELADO",
            curso__nivel_formacao="GRADUACAO",
            publicado=False,
            termino=None,
            make_m2m=True,
        )
        for periodo in range(1, 7):
            mommy.make(
                "cursos.DisciplinaCurso",
                curso=cls.curso,
                periodo=periodo,
                make_m2m=True,
            )

        cls.pessoa = mommy.make(
            PessoaFisica,
            nome="John Doe",
            user__username="user",
            user__is_staff=True,
            user__is_active=True,
        )
        cls.pessoa.user.set_password("123")
        cls.pessoa.user.save()

    def setUp(self) -> None:
        self.admin_group = Group.objects.get(
            name="Administradores Sistêmicos de Cursos"
        )
        self.pessoa.user.groups.add(self.admin_group)
        self.pessoa.user.save()
        self.client.login(username=self.pessoa.user.username, password="123")

    def test_editar_cursos(self):
        url_curso = reverse("curso", kwargs={"pk": self.curso.pk})
        url_curso_update = reverse("cursonocampus_update", kwargs={"pk": self.curso.pk})

        response = self.client.get(url_curso)
        self.assertContains(response, self.curso.curso.nome)
        self.assertContains(response, url_curso_update)

        response = self.client.get(url_curso_update)
        self.assertContains(response, self.curso.curso.nome)

        data = {
            "perfil_libras": "https://www.youtube.com/embed/kt1_3cCRmRA",
            "video_catalogo": "https://www.youtube.com/embed/b7W1DQdGkEg",
        }
        response = self.client.post(url_curso_update, data=data, follow=True)
        self.assertContains(response, self.curso.curso.nome)
        self.assertContains(response, "Curso atualizado com sucesso")

    def test_editar_cursos_nao_autorizado(self):
        url_curso = reverse("curso", kwargs={"pk": self.curso.pk})
        url_curso_update = reverse("cursonocampus_update", kwargs={"pk": self.curso.pk})

        self.client.logout()

        response = self.client.get(url_curso)
        self.assertContains(response, self.curso.curso.nome)
        self.assertNotContains(response, url_curso_update)

        response = self.client.get(url_curso_update)
        self.assertContains(response, "", status_code=403)

        data = {
            "perfil_libras": "https://www.youtube.com/embed/kt1_3cCRmRA",
            "video_catalogo": "https://www.youtube.com/embed/b7W1DQdGkEg",
        }
        response = self.client.post(url_curso_update, data=data, follow=True)
        self.assertContains(response, "", status_code=403)
