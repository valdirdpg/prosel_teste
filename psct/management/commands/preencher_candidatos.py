import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from base.models import PessoaFisica
from candidatos.models import Caracterizacao


class Command(BaseCommand):
    help = "Preenche dados complementares da Pré-matrícula"

    def add_arguments(self, parser):
        parser.add_argument("usuario", nargs="+", type=int)

    def handle(self, *args, **options):
        if not settings.DEBUG:
            print("Comando não permitido!")
        else:
            dados = {
                "certidao": "Folha 123",
                "rg": "1234567",
                "orgao_expeditor": "SSP",
                "data_expedicao": datetime.datetime(2010, 1, 1, 0, 0),
                "profissao": "Estudante",
                "tipo_sanguineo": "O_POS",
                "atualizado_em": datetime.datetime.now(),
            }

            dados_carac = {
                "mae_falecida": False,
                "quantidade_notebooks_id": 0,
                "trabalho_situacao_id": 9,
                "tipo_area_escola_ensino_fundamental_id": 5,
                "contribuintes_renda_familiar_id": 11,
                "escola_ensino_fundamental_id": 1,
                "estado_civil_pais_id": 7,
                "quantidade_computadores": 1,
                "quantidade_netbooks": 0,
                "responsavel_financeir_trabalho_situacao_id": 6,
                "mae_nivel_escolaridade_id": 16,
                "responsavel_financeiro_nivel_escolaridade_id": 16,
                "qtd_filhos": 0,
                "qtd_pessoas_domicilio": 5,
                "ensino_fundamental_conclusao": 2016,
                "escolaridade_id": 14,
                "possui_conhecimento_informatica": True,
                "meio_transporte_utilizado_id": 13,
                "local_acesso_internet": "Casa",
                "estado_civil_id": 6,
                "companhia_domiciliar_id": 7,
                "pai_falecido": False,
                "pai_nivel_escolaridade_id": 16,
                "responsavel_financeiro_id": 11,
                "frequencia_acesso_internet": 1,
                "possui_conhecimento_idiomas": False,
                "tipo_servico_saude_id": 3,
                "nome_escola_ensino_fundamental": "EEAA",
                "tipo_imovel_residencial_id": 8,
                "possui_necessidade_especial": False,
                "quantidade_smartphones": 1,
                "tipo_area_residencial_id": 5,
                "renda_bruta_familiar": 3000.00,
                "aluno_exclusivo_rede_publica": True,
                "ficou_tempo_sem_estudar": False,
                "raca_id": 3,
                "atualizado_em": datetime.datetime.now(),
            }

            for usuario in options["usuario"]:
                p = PessoaFisica.objects.filter(user__username=str(usuario))
                p.update(**dados)

                c = Caracterizacao.objects.filter(candidato=p).last()
                if c is None and p.exists():
                    c = Caracterizacao()
                    c.candidato_id = p.last().pk
                    c.__dict__.update(**dados_carac)
                    c.save()
                print(p)
