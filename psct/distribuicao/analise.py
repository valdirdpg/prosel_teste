from django.db.models import Q

from psct.distribuicao.base import RedistribuirItemUsuario
from psct.models import analise as models


class RedistribuirInscricao(RedistribuirItemUsuario):
    def __init__(self, fase, source, target, size):
        super().__init__(source, target, size)
        self.fase = fase

    def get_userbox_collection(self, userbox):
        return userbox.inscricoes


class RedistribuirInscricaoAvaliador(RedistribuirInscricao):
    userbox_class = models.MailBoxAvaliadorInscricao

    def get_userbox_kwargs(self, usuario):
        return {"fase": self.fase, "avaliador": usuario}

    def get_source_itens(self, source):
        return (
            super()
            .get_source_itens(source)
            .filter(
                Q(avaliacoes_avaliador__isnull=True)
                | (
                    Q(avaliacoes_avaliador__isnull=False)
                    & ~Q(avaliacoes_avaliador__avaliador=source)
                )
            )
            .distinct()
        )


class RedistribuirInscricaoHomologador(RedistribuirInscricao):
    userbox_class = models.MailBoxHomologadorInscricao

    def get_userbox_kwargs(self, usuario):
        return {"fase": self.fase, "homologador": usuario}

    def get_source_itens(self, source):
        return (
            super()
            .get_source_itens(source)
            .filter(avaliacoes_homologador__isnull=True)
            .distinct()
        )
