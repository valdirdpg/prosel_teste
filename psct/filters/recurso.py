from ajax_select import fields as ajax_fields
from django.db import models

from base.custom.filters import FieldFilter, Filter
from psct.models.recurso import Edital, Recurso


class SituacaoRecursoFilter(Filter):
    title = "Situação"
    parameter_name = "situacao"

    def get_choices(self, queryset):
        return (
            ("", "--------"),
            (1, "Sem Avaliadores"),
            (9, "Avaliadores Incompletos"),
            (2, "Com Avaliação Pendente"),
            (3, "Com Avaliação não concluída"),
            (4, "Sem Homologador"),
            (5, "Aguardando Homologador"),
            (6, "Homologado"),
            (7, "Deferidos"),
            (8, "Indeferidos"),
        )

    def get_queryset(self, queryset):
        value = self.get_value()
        if value:
            value = int(value)
            qs = queryset
            if value == 1:  # Sem avaliadores
                qs = qs.filter(mailbox_avaliadores__isnull=True)
            elif value == 2:  # Com avaliação pendente
                qs = qs.annotate(
                    avaliacoes=models.Sum(
                        models.Case(
                            models.When(pareceres_avaliadores__isnull=False, then=1),
                            default=0,
                            output_field=models.IntegerField(),
                        )
                    )
                )
                return qs.exclude(avaliacoes=models.F("fase__quantidade_avaliadores"))
            elif value == 3:  # Com Avaliação não concluída
                qs = qs.annotate(
                    avaliacoes=models.Sum(
                        models.Case(
                            models.When(
                                pareceres_avaliadores__isnull=False,
                                pareceres_avaliadores__concluido=False,
                                then=1,
                            ),
                            default=0,
                            output_field=models.IntegerField(),
                        )
                    )
                )
                return qs.filter(avaliacoes__gte=1)
            elif value == 4:  # Sem homologador
                qs = qs.filter(mailbox_homologadores__isnull=True)
            elif value == 5:  # Aguardando Homologador
                qs = qs.annotate(
                    avaliacoes=models.Sum(
                        models.Case(
                            models.When(pareceres_avaliadores__isnull=False, then=1),
                            default=0,
                            output_field=models.IntegerField(),
                        )
                    )
                )
                return qs.filter(
                    avaliacoes=models.F("fase__quantidade_avaliadores"),
                    mailbox_homologadores__isnull=False,
                    pareceres_homologadores__isnull=True,
                )
            elif value == 6:  # Homologados
                qs = qs.filter(pareceres_homologadores__isnull=False)
            elif value == 7:  # Deferidos
                qs = qs.filter(
                    pareceres_homologadores__isnull=False,
                    pareceres_homologadores__aceito=True,
                )
            elif value == 8:  # Indeferidos
                qs = qs.filter(
                    pareceres_homologadores__isnull=False,
                    pareceres_homologadores__aceito=False,
                )
            elif value == 9:  # Avaliadores Incompletos
                qs = qs.annotate(
                    avaliadores=models.Count("mailbox_avaliadores", distinct=True)
                )
                return qs.exclude(avaliadores=models.F("fase__quantidade_avaliadores"))
            return qs.distinct()
        return queryset


class AvaliadorFilter(Filter):
    parameter_name = "avaliador"
    title = "Avaliador"

    def get_choices(self, queryset):
        return []

    def get_queryset(self, queryset):
        value = self.get_value()
        if value:
            return queryset.filter(
                mailbox_avaliadores__avaliador__username=value
            ).distinct()
        return queryset

    def get_form_field(self, queryset):
        return ajax_fields.AutoCompleteSelectField(
            "servidores", required=False, help_text="", label=self.title
        )


class HomologadorFilter(AvaliadorFilter):
    parameter_name = "homologador"
    title = "Homologador"

    def get_queryset(self, queryset):
        value = self.get_value()
        if value:
            return queryset.filter(
                mailbox_homologadores__homologador__username=value
            ).distinct()
        return queryset


class EditalPSCTFilter(FieldFilter):
    model = Recurso
    field_path = "fase__edital"

    def __init__(self, request):
        super().__init__(self.model, self.field_path, request)

    def get_choices(self, queryset):
        dash = [("", "--------")]
        qs = Edital.objects.filter(processo_inscricao__isnull=False).distinct()
        choices = [(e.id, e) for e in qs]
        return dash + choices


class ServidorFilter(Filter):
    parameter_name = "servidor"
    title = "Servidor"

    def __init__(self, request):
        super().__init__(request)

    def get_choices(self, queryset):
        return []

    def get_queryset(self, queryset):
        value = self.get_value()
        if value:
            return queryset.filter(grupo__user__username=value).distinct()
        return queryset

    def get_form_field(self, queryset):
        return ajax_fields.AutoCompleteSelectField(
            "servidores", required=False, help_text="", label=self.title
        )
