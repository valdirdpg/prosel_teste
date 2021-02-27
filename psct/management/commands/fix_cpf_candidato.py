from collections import Iterable

from django.contrib.admin.utils import NestedObjects
from django.core.management.base import BaseCommand
from django.db import transaction

from base.cleaners import remove_simbolos_cpf
from base.models import PessoaFisica
from processoseletivo.models import Candidato as CandidatoPS, Inscricao as InscricaoPS
from psct.models.analise import Inscricao as InscricaoPSCT, InscricaoPreAnalise
from psct.models.candidato import Candidato as CandidatoPSCT
from psct.models.questionario import RespostaModelo


def str_item(item, stdout):
    if not isinstance(item, Iterable):
        stdout.write(f"\t{type(item)} - {item}")
    else:
        for sub_item in item:
            str_item(sub_item, stdout)


def exclude_item(obj, stdout):
    collector = NestedObjects(using="default")
    collector.collect([obj])
    stdout.write("Os seguintes objetos serão excluídos:")
    for item in collector.nested():
        str_item(item, stdout)
    stdout.write("Os seguintes objetos impedem a exclusão:")
    for item in collector.protected:
        str_item(item, stdout)
    continuar = input("Deseja continuar: [s/n] ")
    if continuar == "s":
        stdout.write(str(obj.delete()))
        stdout.write("Excluído com sucesso")


class Command(BaseCommand):
    help = "Consertar problema com CPF de candidato"

    def add_arguments(self, parser):
        parser.add_argument("cpf", type=str)

    @transaction.atomic()
    def handle(self, *args, **options):
        CPF_CERTO = options["cpf"]
        CPF_ERRADO = remove_simbolos_cpf(CPF_CERTO)
        pessoa_correta = PessoaFisica.objects.get(cpf=CPF_CERTO)
        pessoa_errada = PessoaFisica.objects.filter(cpf=CPF_ERRADO).first()

        if not pessoa_errada:
            self.stdout.write("Pessoa física com dados errados não encontrada")
            return

        continuar = input(f"{pessoa_correta}, continuar: [s/n] ")
        if continuar != "s":
            self.stdout.write("Encerrando sem fazer alterações")
            return

        candidato_ps_correto = CandidatoPS.objects.get(pessoa=pessoa_correta)
        candidato_ps_errado = CandidatoPS.objects.filter(pessoa=pessoa_errada).first()

        if candidato_ps_errado:
            InscricaoPS.objects.filter(candidato=candidato_ps_errado).update(
                candidato=candidato_ps_correto
            )
            exclude_item(candidato_ps_errado, self.stdout)

        candidato_psct_errado = CandidatoPSCT.objects.filter(cpf=CPF_ERRADO).first()

        if not pessoa_errada:
            self.stdout.write("Candidato PSCT com dados errados não encontrado")
            return

        candidato_psct_correto = CandidatoPSCT.objects.filter(cpf=CPF_CERTO).first()

        if not candidato_psct_correto:
            candidato_psct_correto = CandidatoPSCT()
            candidato_psct_correto.pessoafisica_ptr = pessoa_correta
            candidato_psct_correto.__dict__.update(pessoa_correta.__dict__)
            candidato_psct_correto.save()

        InscricaoPSCT.objects.filter(candidato=candidato_psct_errado).update(
            candidato=candidato_psct_correto
        )
        InscricaoPreAnalise.objects.filter(candidato=candidato_psct_errado).update(
            candidato=candidato_psct_correto
        )
        RespostaModelo.objects.filter(candidato=candidato_psct_errado).update(
            candidato=candidato_psct_correto
        )

        exclude_item(pessoa_errada, self.stdout)
