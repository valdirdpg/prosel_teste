import datetime
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from . import recipes
from .. import models
from ..choices import CertidaoCivil, Nacionalidade


class PessoaFisicaTestCase(TestCase):
    def test_str_deveria_ter_nome_e_cpf(self):
        pessoa = recipes.pessoa_fisica.make()
        self.assertEqual(f"{pessoa.nome.upper()} (CPF: {pessoa.cpf})", str(pessoa))

    def test_endereco_completo_com_complemento_deveria_ter_todos_os_dados(self):
        pessoa = recipes.pessoa_fisica.make(
            complemento_endereco="Complemento"
        )
        self.assertEqual(
            "{}, {} - {} - {}, {}/{}".format(
                pessoa.logradouro,
                pessoa.numero_endereco,
                pessoa.complemento_endereco,
                pessoa.bairro,
                pessoa.municipio,
                pessoa.uf,
            ),
            pessoa.endereco_completo
        )

    def test_endereco_completo_sem_complemento_deveria_ter_todos_os_dados(self):
        pessoa = recipes.pessoa_fisica.make()
        self.assertEqual(
            "{}, {} - {}, {}/{}".format(
                pessoa.logradouro,
                pessoa.numero_endereco,
                pessoa.bairro,
                pessoa.municipio,
                pessoa.uf,
            ),
            pessoa.endereco_completo
        )

    @mock.patch("base.models.configs.PortalConfig")
    @mock.patch("base.models.utils.dias_entre")
    def test_is_atualizado_recentemente_deveria_ser_verdadeiro_para_numero_menor(
            self, dias_entre, config
    ):
        dias_entre.return_value = 1
        config.DIAS_ATUALIZACAO_DADOS = 2
        pessoa = recipes.pessoa_fisica.make()
        self.assertTrue(pessoa.is_atualizado_recentemente())

    @mock.patch("base.models.configs.PortalConfig")
    @mock.patch("base.models.utils.dias_entre")
    def test_is_atualizado_recentemente_deveria_ser_falso_para_numero_igual(
            self, dias_entre, config
    ):
        dias_entre.return_value = 1
        config.DIAS_ATUALIZACAO_DADOS = 1
        pessoa = recipes.pessoa_fisica.make()
        self.assertFalse(pessoa.is_atualizado_recentemente())

    @mock.patch("base.models.configs.PortalConfig")
    @mock.patch("base.models.utils.dias_entre")
    def test_is_atualizado_recentemente_deveria_ser_falso_para_numero_maior(
            self, dias_entre, config
    ):
        dias_entre.return_value = 2
        config.DIAS_ATUALIZACAO_DADOS = 1
        pessoa = recipes.pessoa_fisica.make()
        self.assertFalse(pessoa.is_atualizado_recentemente())

    @mock.patch.object(models.PessoaFisica, "_has_certidao_civil", return_value=True)
    @mock.patch.object(models.PessoaFisica, "_has_contatos", return_value=True)
    @mock.patch.object(models.PessoaFisica, "is_atualizado_recentemente", return_value=True)
    def test_has_dados_suap_completos_deveria_ser_verdadeiro_se_atender_a_todos_os_criterios(
            self, is_atualizado_recentemente, _has_contatos, _has_certidao_civil  # noqa
    ):
        pessoa = recipes.pessoa_fisica.make()
        self.assertTrue(pessoa.has_dados_suap_completos())

    @mock.patch.object(models.PessoaFisica, "_has_certidao_civil", return_value=False)
    @mock.patch.object(models.PessoaFisica, "_has_contatos", return_value=True)
    @mock.patch.object(models.PessoaFisica, "is_atualizado_recentemente", return_value=True)
    def test_has_dados_suap_completos_deveria_ser_falso_sem_certidao_civil(
            self, is_atualizado_recentemente, _has_contatos, _has_certidao_civil  # noqa
    ):
        pessoa = recipes.pessoa_fisica.make()
        self.assertFalse(pessoa.has_dados_suap_completos())

    @mock.patch.object(models.PessoaFisica, "_has_certidao_civil", return_value=True)
    @mock.patch.object(models.PessoaFisica, "_has_contatos", return_value=False)
    @mock.patch.object(models.PessoaFisica, "is_atualizado_recentemente", return_value=True)
    def test_has_dados_suap_completos_deveria_ser_falso_sem_contatos(
            self, is_atualizado_recentemente, _has_contatos, _has_certidao_civil  # noqa
    ):
        pessoa = recipes.pessoa_fisica.make()
        self.assertFalse(pessoa.has_dados_suap_completos())

    @mock.patch.object(models.PessoaFisica, "_has_certidao_civil", return_value=True)
    @mock.patch.object(models.PessoaFisica, "_has_contatos", return_value=True)
    @mock.patch.object(models.PessoaFisica, "is_atualizado_recentemente", return_value=False)
    def test_has_dados_suap_completos_deveria_ser_falso_sem_ser_atualizado_recentemente(
            self, is_atualizado_recentemente, _has_contatos, _has_certidao_civil  # noqa
    ):
        pessoa = recipes.pessoa_fisica.make()
        self.assertFalse(pessoa.has_dados_suap_completos())

    def test_has_rg_deveria_ser_valido_se_todos_os_dados_estao_preenchidos(self):
        pessoa = recipes.pessoa_fisica.make(
            rg=123,
            orgao_expeditor="SSP",
            orgao_expeditor_uf="PB",
            data_expedicao=datetime.date.today()
        )
        self.assertTrue(pessoa._has_rg())

    def test_has_rg_nao_deveria_ser_valido_se_um_dos_dados_nao_estao_preenchidos(self):
        pessoa = recipes.pessoa_fisica.make()
        self.assertFalse(pessoa._has_rg())

    def test_has_certidao_civil_deveria_ser_valido_se_todos_os_dados_estao_preenchidos(self):
        pessoa = recipes.pessoa_fisica.make(
            certidao="123",
            certidao_data=datetime.date.today(),
            certidao_livro="Livro",
            certidao_folha="Folha",
            certidao_tipo=CertidaoCivil.CASAMENTO.name,
        )
        self.assertTrue(pessoa._has_certidao_civil())

    def test_has_certidao_civil_deveria_ser_valido_se_um_dos_dados_nao_estao_preenchidos(self):
        pessoa = recipes.pessoa_fisica.make()
        self.assertFalse(pessoa._has_certidao_civil())

    def test_has_contatos_deveria_ser_valido_se_todos_os_dados_estao_preenchidos(self):
        pessoa = recipes.pessoa_fisica.make(
            telefone="123",
            email="email@email.br",
        )
        self.assertTrue(pessoa._has_contatos())

    def test_has_contatos_civil_deveria_ser_valido_se_um_dos_dados_nao_estao_preenchidos(self):
        pessoa = recipes.pessoa_fisica.make()
        self.assertFalse(pessoa._has_contatos())

    def test_rg_completo_deveria_retornar_todos_os_dados(self):
        pessoa = recipes.pessoa_fisica.make(
            rg=123,
            orgao_expeditor="SSP",
            orgao_expeditor_uf="PB",
            data_expedicao=datetime.date.today()
        )
        self.assertEqual(
            (
                f"{pessoa.rg} - {pessoa.orgao_expeditor}/{pessoa.orgao_expeditor_uf} - "
                f'{pessoa.data_expedicao.strftime("%d/%m/%Y")}'
            ),
            pessoa.rg_completo
        )

    def test_rg_completo_deveria_retornar_nao_informado(self):
        pessoa = recipes.pessoa_fisica.make()
        self.assertEqual("Não Informado", pessoa.rg_completo)

    def test_titulo_eleitor_deveria_retornar_todos_os_dados(self):
        pessoa = recipes.pessoa_fisica.make(
            numero_titulo_eleitor="1234",
            zona_titulo_eleitor="4567",
            secao_titulo_eleitor="7890"
        )
        self.assertEqual(
            (
                f"{pessoa.numero_titulo_eleitor}, Zona {pessoa.zona_titulo_eleitor}, "
                f"Seção {pessoa.secao_titulo_eleitor}"
            ),
            pessoa.titulo_eleitor
        )

    def test_titulo_eleitor_deveria_retornar_nao_informado(self):
        pessoa = recipes.pessoa_fisica.make()
        self.assertEqual("Não Informado", pessoa.titulo_eleitor)

    def test_naturalidade_completa_deveria_retornar_todos_os_dados(self):
        pessoa = recipes.pessoa_fisica.make(
            naturalidade_uf="PB",
            naturalidade="Cidade",
        )
        self.assertEqual(
            f"{pessoa.naturalidade}/{pessoa.naturalidade_uf}".upper(),
            pessoa.naturalidade_completa
        )

    def test_naturalidade_completa_deveria_retornar_nao_informado(self):
        pessoa = recipes.pessoa_fisica.make(naturalidade="Cidade")
        self.assertEqual(f"{pessoa.naturalidade}".upper(), pessoa.naturalidade_completa)

    def test_validate_naturalidade_deveria_validar_preenchimento_brasileiros(self):
        pessoa = recipes.pessoa_fisica.make(nacionalidade=Nacionalidade.BRASILEIRA.name)
        self.assertDictEqual(
            {
                "naturalidade": (
                    "Este campo deve ser preenchido para pessoas de nacionalidade Brasileira."
                )
            },
            pessoa.validate_naturalidade()
        )

    def test_validate_naturalidade_deveria_validar_preenchimento_estrangeiros(self):
        pessoa = recipes.pessoa_fisica.make(
            nacionalidade=Nacionalidade.ESTRANGEIRA.name,
            naturalidade="Cidade qualuqer",
        )
        self.assertDictEqual(
            {
                "naturalidade": (
                    "Este campo não deve ser preenchido para pessoas de nacionalidade Estrangeira."
                )
            },
            pessoa.validate_naturalidade()
        )

    def test_validate_naturalidade_deveria_ser_valido_para_brasileiros(self):
        pessoa = recipes.pessoa_fisica.make(
            nacionalidade=Nacionalidade.BRASILEIRA.name,
            naturalidade="Cidade qualquer",
        )
        self.assertDictEqual({}, pessoa.validate_naturalidade())

    def test_validate_naturalidade_deveria_ser_valido_para_estrangeiros(self):
        pessoa = recipes.pessoa_fisica.make(
            nacionalidade=Nacionalidade.ESTRANGEIRA.name,
        )
        self.assertDictEqual({}, pessoa.validate_naturalidade())

    def test_validate_naturalidade_uf_deveria_validar_preenchimento_brasileiros(self):
        pessoa = recipes.pessoa_fisica.make(nacionalidade=Nacionalidade.BRASILEIRA.name)
        self.assertDictEqual(
            {
                "naturalidade_uf": (
                    "Este campo deve ser preenchido para pessoas de nacionalidade Brasileira."
                )
            },
            pessoa.validate_naturalidade_uf()
        )

    def test_validate_naturalidade_uf_deveria_validar_preenchimento_estrangeiros(self):
        pessoa = recipes.pessoa_fisica.make(
            nacionalidade=Nacionalidade.ESTRANGEIRA.name,
            naturalidade_uf="PB",
        )
        self.assertDictEqual(
            {
                "naturalidade_uf": (
                    "Este campo não deve ser preenchido para pessoas de nacionalidade Estrangeira."
                )
            },
            pessoa.validate_naturalidade_uf()
        )

    def test_validate_naturalidade_uf_deveria_ser_valido_para_brasileiros(self):
        pessoa = recipes.pessoa_fisica.make(
            nacionalidade=Nacionalidade.BRASILEIRA.name,
            naturalidade_uf="PB",
        )
        self.assertDictEqual({}, pessoa.validate_naturalidade_uf())

    def test_validate_naturalidade_uf_deveria_ser_valido_para_estrangeiros(self):
        pessoa = recipes.pessoa_fisica.make(
            nacionalidade=Nacionalidade.ESTRANGEIRA.name,
        )
        self.assertDictEqual({}, pessoa.validate_naturalidade_uf())

    @mock.patch("base.models.is_maior_idade", return_value=True)
    @mock.patch("base.models.configs.PortalConfig")
    def test_validate_titulo_eleitor_deveria_validar_numero_titulo_eleitor_para_maiores(
            self, config, is_maior_idade  # noqa
    ):
        config.MAIORIDADE = 1
        pessoa = recipes.pessoa_fisica.make()
        errors = pessoa.validate_titulo_eleitor()
        self.assertIn("numero_titulo_eleitor", errors)
        self.assertEqual(
            f"Obrigatório para maiores de {config.MAIORIDADE} anos.",
            errors["numero_titulo_eleitor"]
        )

    @mock.patch("base.models.is_maior_idade", return_value=True)
    @mock.patch("base.models.configs.PortalConfig")
    def test_validate_titulo_eleitor_deveria_validar_zona_titulo_eleitor_para_maiores(
            self, config, is_maior_idade  # noqa
    ):
        config.MAIORIDADE = 1
        pessoa = recipes.pessoa_fisica.make()
        errors = pessoa.validate_titulo_eleitor()
        self.assertIn("zona_titulo_eleitor", errors)
        self.assertEqual(
            f"Obrigatório para maiores de {config.MAIORIDADE} anos.",
            errors["zona_titulo_eleitor"]
        )

    @mock.patch("base.models.is_maior_idade", return_value=True)
    @mock.patch("base.models.configs.PortalConfig")
    def test_validate_titulo_eleitor_deveria_validar_secao_titulo_eleitor_para_maiores(
            self, config, is_maior_idade  # noqa
    ):
        config.MAIORIDADE = 1
        pessoa = recipes.pessoa_fisica.make()
        errors = pessoa.validate_titulo_eleitor()
        self.assertIn("secao_titulo_eleitor", errors)
        self.assertEqual(
            f"Obrigatório para maiores de {config.MAIORIDADE} anos.",
            errors["secao_titulo_eleitor"]
        )

    @mock.patch("base.models.is_maior_idade", return_value=True)
    def test_validate_titulo_eleitor_deveria_validar_numero_titulo_eleitor(
            self, is_maior_idade  # noqa
    ):
        pessoa = recipes.pessoa_fisica.make(numero_titulo_eleitor="123ABC")
        errors = pessoa.validate_titulo_eleitor()
        self.assertIn("numero_titulo_eleitor", errors)
        self.assertEqual("Deve conter apenas números.", errors["numero_titulo_eleitor"])

    @mock.patch("base.models.is_maior_idade", return_value=True)
    def test_validate_titulo_eleitor_deveria_validar_zona_titulo_eleitor(
            self, is_maior_idade  # noqa
    ):
        pessoa = recipes.pessoa_fisica.make(zona_titulo_eleitor="123ABC")
        errors = pessoa.validate_titulo_eleitor()
        self.assertIn("zona_titulo_eleitor", errors)
        self.assertEqual("Deve conter apenas números.", errors["zona_titulo_eleitor"])

    @mock.patch("base.models.is_maior_idade", return_value=True)
    def test_validate_titulo_eleitor_deveria_validar_secao_titulo_eleitor(
            self, is_maior_idade  # noqa
    ):
        pessoa = recipes.pessoa_fisica.make(secao_titulo_eleitor="123ABC")
        errors = pessoa.validate_titulo_eleitor()
        self.assertIn("secao_titulo_eleitor", errors)
        self.assertEqual("Deve conter apenas números.", errors["secao_titulo_eleitor"])

    def test_validate_titulo_eleitor_deveria_ser_valido(self):
        pessoa = recipes.pessoa_fisica.make(
            secao_titulo_eleitor="1234",
            zona_titulo_eleitor="1234",
            numero_titulo_eleitor="1234",
        )
        self.assertEqual({}, pessoa.validate_titulo_eleitor())

    @mock.patch.object(models.PessoaFisica, "validate_naturalidade")
    @mock.patch.object(models.PessoaFisica, "validate_naturalidade_uf")
    def test_clean_deveria_validar_naturalidade_e_uf(
            self, validate_naturalidade, validate_naturalidade_uf
    ):
        validate_naturalidade.return_value = {"field": "message"}
        validate_naturalidade_uf.return_value = {"field": "message"}
        pessoa = recipes.pessoa_fisica.make()
        with self.assertRaises(ValidationError):
            pessoa.clean()

        validate_naturalidade.assert_called_once()
        validate_naturalidade_uf.assert_called_once()

    @mock.patch.object(models.PessoaFisica, "validate_naturalidade")
    @mock.patch.object(models.PessoaFisica, "validate_naturalidade_uf")
    def test_clean_nao_deveria_lancar_excecao_se_estiver_valido(
            self, validate_naturalidade, validate_naturalidade_uf
    ):
        validate_naturalidade.return_value = {}
        validate_naturalidade_uf.return_value = {}
        pessoa = recipes.pessoa_fisica.make()
        self.assertIsNone(pessoa.clean())

        validate_naturalidade.assert_called_once()
        validate_naturalidade_uf.assert_called_once()

    def test_save_deveria_atualizar_o_email_do_usuario_quando_for_diferente(self):
        pessoa = recipes.pessoa_fisica.prepare(
            email="pessoa@email.br",
            user=recipes.user.make(email="user@email.br")
        )
        pessoa.save()
        self.assertEqual(pessoa.user.email, pessoa.email)

    def test_save_nao_deveria_atualizar_o_email_do_usuario_quando_for_igual(self):
        pessoa = recipes.pessoa_fisica.prepare(
            email="pessoa@email.br",
            user=recipes.user.make(email="pessoa@email.br")
        )
        pessoa.save()
        self.assertEqual(pessoa.user.email, pessoa.email)

    def test_save_deveria_atualizar_nome_do_usuario(self):
        pessoa = recipes.pessoa_fisica.prepare(
            email="pessoa@email.br",
            user=recipes.user.make(email="user@email.br")
        )
        pessoa.save()
        self.assertEqual(pessoa.user.first_name, pessoa.nome.split()[0])
        self.assertEqual(pessoa.user.last_name, pessoa.nome.split()[-1])

    def test_save_nao_deveria_atualizar_nome_do_usuario_se_nao_existe(self):
        user = recipes.user.make(first_name="", last_name="")
        pessoa = recipes.pessoa_fisica.prepare(nome="", user=user)
        pessoa.save()
        self.assertEqual("", pessoa.user.first_name)
        self.assertEqual("", pessoa.user.last_name)

    def test_save_nao_deveria_salvar_usuario_se_nao_estiver_salvo_ainda(self):
        pessoa = recipes.pessoa_fisica.prepare()
        self.assertIsNone(pessoa.save())
        self.assertIsNone(pessoa.user_id)

    def test_save_deveria_salvar_usuario_se_existir(self):  # noqa
        user = recipes.user.make()
        user.save = mock.Mock()
        recipes.pessoa_fisica.make(
            user=user
        )
        user.save.assert_called_once()
