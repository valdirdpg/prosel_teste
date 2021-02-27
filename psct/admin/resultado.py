from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from base.custom.widget import SideBarMenu
from psct.models.resultado import ResultadoPreliminar


class ResultadoPreliminarEditalFilter(admin.SimpleListFilter):
    title = "Resultado Preliminar de Edital"
    parameter_name = "resultado_preliminar"

    def lookups(self, request, model_admin):
        return [(0, "Não"), (1, "Sim")]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            v = not bool(int(value))
            return queryset.filter(resultadopreliminarhomologado__isnull=v)
        return queryset


class ResultadoFinalFilter(admin.SimpleListFilter):
    title = "Resultado de Edital"
    parameter_name = "resultado"

    def lookups(self, request, model_admin):
        return [(0, "Não"), (1, "Sim")]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            v = not bool(int(value))
            return queryset.filter(resultadofinal__isnull=v)
        return queryset


class ResultadoPreliminarAdmin(admin.ModelAdmin):
    list_display = ("id", "edital_display", "data_cadastro", "acoes")
    list_filter = (
        ("fase__edital", admin.RelatedOnlyFieldListFilter),
        ResultadoPreliminarEditalFilter,
        ResultadoFinalFilter,
    )
    list_display_links = None

    def has_change_permission(self, request, obj=None):
        if obj:
            return False
        return super().has_change_permission(request, obj)

    def has_add_permission(self, request):
        return False

    @mark_safe
    def acoes(self, obj):
        menu = SideBarMenu("Opções")
        menu.add(
            "Exportar para arquivo",
            reverse("resultado_file_psct", kwargs=dict(resultado_pk=obj.pk)),
        )

        if not hasattr(obj.fase.edital, "resultado_preliminar"):
            menu.add(
                "Definir como resultado preliminar do edital",
                reverse("homologar_resultado_preliminar_psct", kwargs=dict(pk=obj.pk)),
            )
        else:
            resultado_final_definido = hasattr(obj.fase.edital, "resultado")

            if (
                obj.fase.edital.resultado_preliminar.resultado == obj
                and not resultado_final_definido
            ):
                menu.add(
                    "Remover resultado preliminar do edital",
                    reverse(
                        "remover_homologacao_resultado_preliminar_psct",
                        kwargs=dict(pk=obj.pk),
                    ),
                )

            if not resultado_final_definido:
                menu.add(
                    "Definir como resultado final do edital",
                    reverse("add_resultado_psct", kwargs=dict(pk=obj.pk)),
                )
            else:
                if obj.fase.edital.resultado.resultado == obj:
                    menu.add(
                        "Remover resultado de edital",
                        reverse("delete_resultado_psct", kwargs=dict(pk=obj.pk)),
                    )

        menu.add(
            "Visualizar vagas",
            reverse("view_vagas_resultado_psct", kwargs=dict(pk=obj.pk)),
        )
        return menu.render()

    acoes.short_description = "Ações"

    def edital_display(self, obj):
        edital = obj.fase.edital
        return f"{edital.numero}/{edital.ano}"

    edital_display.short_description = "Edital"


admin.site.register(ResultadoPreliminar, ResultadoPreliminarAdmin)
