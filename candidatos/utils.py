from ifpb_django_permissions.perms import in_any_groups

from processoseletivo.models import Etapa
from psct.permissions import CandidatosPSCT
from .permissions import Candidatos


def is_candidato_prematricula(user):
    if not in_any_groups(user, [Candidatos, CandidatosPSCT]):
        return False
    etapas = Etapa.objects.filter(
        encerrada=False,
        publica=True,
        chamadas__inscricoes__candidato__pessoa__user=user,
    ).distinct()
    for etapa in etapas:
        for cronograma in etapa.cronogramas_convocacao.distinct():
            if (
                cronograma.is_manifestacao_interesse()
                and not cronograma.is_encerrado()
                and cronograma.gerenciavel
            ):
                return True
    return False


def is_candidato_prematricula_menu(request):
    return is_candidato_prematricula(request.user)
