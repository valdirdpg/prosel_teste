from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from psct import models


class CriterioAlternativaInline(admin.StackedInline):
    model = models.CriterioAlternativa
    min_num = 2
    extra = 0


class CriterioQuestionarioAdmin(CompareVersionAdmin):
    inlines = [CriterioAlternativaInline]


@admin.register(models.ModeloQuestionario)
class ModeloQuestionarioAdmin(CompareVersionAdmin):
    autocomplete_fields = ("edital",)


admin.site.register(models.CriterioQuestionario, CriterioQuestionarioAdmin)
