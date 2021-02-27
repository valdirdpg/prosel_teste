from django.db.models import Q

from psct.distribuicao import base
from psct.distribuicao.base import RedistribuirItemUsuario
from psct.models import recurso as models


class DistribuidorUsuario(base.DistribuidorItemUsuario):
    def get_userbox_collection(self, userbox):
        return userbox.recursos


class DistribuidorAvaliadores(DistribuidorUsuario):
    userbox_class = models.MailBoxAvaliador

    def get_userbox_kwargs(self, usuario):
        return dict(avaliador=usuario, fase=self.superbox.fase)

    def get_tamanho_subgrupo(self):
        return self.superbox.fase.quantidade_avaliadores

    def get_items(self, superbox):
        return superbox.recursos.filter(mailbox_avaliadores__isnull=True)


class DistribuidorHomologadores(DistribuidorUsuario):
    userbox_class = models.MailBoxHomologador

    def get_tamanho_subgrupo(self):
        return 1

    def get_userbox_kwargs(self, usuario):
        return dict(homologador=usuario, fase=self.superbox.fase)

    def get_items(self, superbox):
        return superbox.recursos.filter(mailbox_homologadores__isnull=True)


class DistribuidorGrupo(base.DistribuidorItemGrupo):
    item_model = models.Recurso

    def __init__(self, fase, coluna, map):
        super().__init__(fase, coluna, map)

    def get_mailbox_collection(self, mailbox):
        return mailbox.recursos

    def get_mailbox_kwargs(self, group):
        return dict(grupo=group, fase=self.fase)


class DistribuidorGrupoAvaliadores(DistribuidorGrupo):
    mailbox_class = models.MailBoxGrupoAvaliadores
    distribuidorusuario_class = DistribuidorAvaliadores

    def get_items(self, filter_value):
        items = super().get_items(filter_value)
        return items.filter(mailbox_grupo_avaliadores__isnull=True)


class DistribuidorGrupoHomologadores(DistribuidorGrupo):
    mailbox_class = models.MailBoxGrupoHomologadores
    distribuidorusuario_class = DistribuidorHomologadores

    def get_items(self, filter_value):
        items = super().get_items(filter_value)
        return items.filter(mailbox_grupo_homologadores__isnull=True)


class RedistribuirRecurso(RedistribuirItemUsuario):
    def __init__(self, fase, source, target, size):
        super().__init__(source, target, size)
        self.fase = fase

    def get_userbox_collection(self, userbox):
        return userbox.recursos


class RedistribuirRecursoAvaliador(RedistribuirRecurso):
    userbox_class = models.MailBoxAvaliador

    def get_userbox_kwargs(self, usuario):
        return {"fase": self.fase, "avaliador": usuario}

    def get_source_itens(self, source):
        return (
            super()
            .get_source_itens(source)
            .filter(
                Q(pareceres_avaliadores__isnull=True)
                | (
                    Q(pareceres_avaliadores__isnull=False)
                    & ~Q(pareceres_avaliadores__avaliador=source)
                )
            )
            .distinct()
        )


class RedistribuirRecursoHomologador(RedistribuirRecurso):
    userbox_class = models.MailBoxHomologador

    def get_userbox_kwargs(self, usuario):
        return {"fase": self.fase, "homologador": usuario}

    def get_source_itens(self, source):
        return (
            super()
            .get_source_itens(source)
            .filter(pareceres_homologadores__isnull=True)
            .distinct()
        )
