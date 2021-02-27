from base.templatetags.base_tags import register


@register.simple_tag
def set_var(valor):
    return valor


@register.simple_tag
def has_errors_inline(inline_formset):
    if any(e for e in inline_formset.formset.errors):
        return True
    return inline_formset.formset._non_form_errors
