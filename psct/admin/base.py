from reversion_compare.admin import CompareVersionAdmin


class EditalPSCTAdmin(CompareVersionAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        qs = form.base_fields["edital"].queryset
        form.base_fields["edital"].queryset = qs.filter(
            processo_inscricao__isnull=False
        ).distinct()
        return form
