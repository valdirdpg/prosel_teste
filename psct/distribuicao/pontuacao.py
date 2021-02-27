from psct.distribuicao.base import RedistribuirItemUsuario
from psct.models import pontuacao as models


class RedistribuirInscricao(RedistribuirItemUsuario):
    def __init__(self, fase, source, target, size):
        super().__init__(source, target, size)
        self.fase = fase

    def get_userbox_collection(self, userbox):
        return userbox.inscricoes


class RedistribuirInscricaoAvaliador(RedistribuirInscricao):
    userbox_class = models.MailboxPontuacaoAvaliador

    def get_userbox_kwargs(self, usuario):
        return {"fase": self.fase, "avaliador": usuario}

    def get_source_itens(self, source):
        return (
            super()
            .get_source_itens(source)
            .filter(pontuacoes_avaliadores__isnull=True)
            .distinct()
        )


class RedistribuirInscricaoHomologador(RedistribuirInscricao):
    userbox_class = models.MailboxPontuacaoHomologador

    def get_userbox_kwargs(self, usuario):
        return {"fase": self.fase, "homologador": usuario}

    def get_source_itens(self, source):
        return (
            super()
            .get_source_itens(source)
            .filter(pontuacoes_homologadores__isnull=True)
            .distinct()
        )
