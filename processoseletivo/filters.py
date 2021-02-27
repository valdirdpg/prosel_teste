from base.custom.filters import FieldFilter
from cursos.models import Campus
from processoseletivo import models


class BaseFieldFilter(FieldFilter):
    def __init__(self, request):
        super().__init__(self.model, self.field_path, request)

    def get_choices(self, queryset):
        return [("", "--------")] + [(o.id, o) for o in queryset]


class EdicaoConfirmacaoInteresseFilter(BaseFieldFilter):
    model = models.ConfirmacaoInteresse
    field_path = "etapa__edicao"

    def get_choices(self, queryset):
        qs = models.Edicao.objects.filter(etapa__isnull=False).distinct()
        return super().get_choices(qs)


class CampusConfirmacaoInteresseFilter(BaseFieldFilter):
    model = models.ConfirmacaoInteresse
    field_path = "inscricao__curso__campus"

    def get_choices(self, queryset):
        if self.request.user.is_superuser or models.is_sistemico(self.request.user):
            qs = Campus.objects.all()
        else:
            qs = self.request.user.lotacoes.all()
        return super().get_choices(qs)
