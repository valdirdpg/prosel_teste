from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from psct.models.consulta import Consulta


class InlineForm(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        for form in self.forms:
            coluna = form.cleaned_data.get("coluna")
            try:
                if (
                    coluna
                    and coluna.entidade != self.instance.entidade
                    and not form.cleaned_data.get("DELETE", False)
                ):
                    raise ValidationError(
                        "Você selecionou uma coluna que não pertence a entidade da consulta"
                    )
            except ContentType.DoesNotExist:
                # O usuário não selecionou a entidade. O sistema informará que o campo é obrigatório
                pass


class PosicaoInlineForm(InlineForm):
    def clean(self):
        super().clean()

        posicoes = [form.cleaned_data.get("posicao") for form in self.forms]

        if len(posicoes) != len(set(posicoes)):
            raise ValidationError("Você digitou duas colunas com números iguais")


class ConsultaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        exclude = []

    def clean_itens_por_pagina(self):
        itens = self.cleaned_data.get("itens_por_pagina")
        if itens:
            if itens > 50:
                raise ValidationError("Limite máximo de 50 itens por página")
        return itens
