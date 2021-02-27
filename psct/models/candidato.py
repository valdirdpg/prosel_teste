import reversion
from django.contrib.auth.models import Group, User

from base import models as models_base
from base.cleaners import remove_simbolos_cpf


@reversion.register(follow=["pessoafisica_ptr"])
class Candidato(models_base.PessoaFisica):
    class Meta:
        verbose_name = "Candidato do PSCT"
        verbose_name_plural = "Candidatos do PSCT"
        permissions = (
            ("admin_can_change_email", "Administrador pode mudar email de candidato"),
            ("list_candidato", "Administrador pode listar candidatos"),
            ("recover_candidato", "Administrador pode recuperar dados de candidato"),
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for inscricao in self.inscricao_set.all():
            inscricao.atualizar_informacoes_candidato()

    def has_inscricao(self):
        has_insc = False
        for inscricao in self.inscricao_set.all():
            if not inscricao.is_cancelada:
                has_insc = True
        return has_insc

    def has_todas_insc_canceladas(self):
        qtd_inscricoes_canceladas = 0
        for inscricao in self.inscricao_set.all():
            if inscricao.is_cancelada:
                qtd_inscricoes_canceladas = qtd_inscricoes_canceladas + 1
        return (len(self.inscricao_set.all()) == qtd_inscricoes_canceladas)



def importar_candidato_sisu(cpf):

    if Candidato.objects.filter(cpf=cpf).exists():
        raise ValueError("Candidato já existe")

    if not models_base.PessoaFisica.objects.filter(cpf=cpf).exists():
        raise ValueError("Pessoa física não existe")

    pessoa = models_base.PessoaFisica.objects.get(cpf=cpf)
    cpf = remove_simbolos_cpf(pessoa.cpf)

    if not pessoa.user:
        user = User.objects.create(
            username=cpf,
            first_name=pessoa.nome.split(" ")[0],
            last_name=pessoa.nome.split(" ")[-1],
            email=pessoa.email,
        )
        pessoa.user = user
        pessoa.save()
    else:
        user = pessoa.user

    if not user.has_usable_password():
        user.set_password(User.objects.make_random_password(length=24))
        user.save()

    if not user.groups.filter(name="Candidatos PSCT").exists():
        group = Group.objects.get(name="Candidatos PSCT")
        user.groups.add(group)

    candidato = Candidato(pessoafisica_ptr=pessoa)
    candidato.__dict__.update(
        {a: v for a, v in pessoa.__dict__.items() if not a.startswith("_")}
    )
    candidato.save()
