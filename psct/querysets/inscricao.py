from django.db.models import Case, When
from django.db.models import QuerySet

from processoseletivo.models import ModalidadeEnum


class ModalidadeQuerySet(QuerySet):
    def ordenação_por_tipo_escola(self):
        from ..models import Modalidade

        return Modalidade.objects.order_by(
            Case(
                When(id=ModalidadeEnum.ampla_concorrencia, then=0),
                default=3,
            ),
            Case(When(id=ModalidadeEnum.deficientes, then=1), default=3),
            Case(When(id=ModalidadeEnum.rurais, then=2), default=3),
            "pk",
        )
