from django.contrib import admin
from django.db.models import Q
from django.utils.safestring import mark_safe

from psct.forms import consulta as forms
from psct.models import consulta


class EntidadeFilterAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)

        class Form(form_class):
            pass

        if "entidade" in Form.base_fields:
            qs = Form.base_fields["entidade"].queryset
            qs = qs.filter(app_label="psct").order_by("model")
            Form.base_fields["entidade"].queryset = qs
            Form.base_fields["entidade"].choices = [("", "-------")] + sorted(
                [(c.id, c) for c in qs], key=lambda x: str(x[1])
            )
        return Form


class FiltroInline(admin.TabularInline):
    model = consulta.RegraFiltro
    min_num = 0
    extra = 0
    formset = forms.InlineForm


class ExclusaoInline(admin.TabularInline):
    model = consulta.RegraExclusao
    min_num = 0
    extra = 0
    formset = forms.InlineForm


class ColunaInline(admin.TabularInline):
    model = consulta.ColunaConsulta
    min_num = 1
    extra = 0
    formset = forms.PosicaoInlineForm


class OrdenacaoInline(admin.TabularInline):
    model = consulta.OrdenacaoConsulta
    min_num = 0
    extra = 0
    formset = forms.PosicaoInlineForm


class ConsultaAdmin(EntidadeFilterAdmin):
    inlines = [FiltroInline, ExclusaoInline, ColunaInline, OrdenacaoInline]
    form = forms.ConsultaForm
    list_display = ("nome", "visualizar")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "user" in form.base_fields:
            form.base_fields["user"].choices = [(request.user.id, request.user)]
        return form

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(Q(user=request.user) | Q(compartilhar=True))
            .distinct()
        )

    def has_change_permission(self, request, obj=None):
        perm = super().has_change_permission(request, obj)
        if perm and obj:
            return obj.user == request.user
        return perm

    def has_delete_permission(self, request, obj=None):
        perm = super().has_delete_permission(request, obj)
        if perm and obj:
            return obj.user == request.user
        return perm

    @mark_safe
    def visualizar(self, obj):
        return '<a href="/psct/consulta/{}/" class="btn btn-default btn-xs">Visualizar</a>'.format(
            obj.id
        )

    visualizar.short_description = "Ações"


class ColunaAdmin(EntidadeFilterAdmin):
    exclude = ("aggregate_nome",)


admin.site.register(consulta.Consulta, ConsultaAdmin)
admin.site.register(consulta.Coluna, ColunaAdmin)
admin.site.register(consulta.Filtro)
