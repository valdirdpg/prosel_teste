from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.forms import models as model_forms
from .models import PessoaFisica


class FieldStyledMixin:
    """
    Tem por objetivo aplicar classes css para os campos do formulário. Inicialmente preparado para os estilos do
    bootstrap. Para usar basta adicionar esta classe como superclasse do seu form (django.forms.Form ou
    django.forms.ModelForm)

    Exemplo de uso:

    class MeuForm(FieldStyledMixin, forms.ModelForm):
        [seu código aqui]

    Parâmetros:
        @field_class: permite passar uma ou mais classes css para ser aplicada ao campo, separadas por espaço
        @styled_fields: lista com o nome dos campos onde o estilo será aplicado.
    """

    field_class = "form-control"
    styled_fields = ["__all__"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_style()

    def apply_style(self):
        # verifica se deve aplicar o estilo para todos os campos
        if self.styled_fields and self.styled_fields[0] == "__all__":
            self.styled_fields = []
            for fname, field in self.fields.items():
                self.styled_fields.append(fname)

        # remove os checkboxes e os radiobuttons da lista
        for field in self.styled_fields:
            ffield = self.fields[field]
            if isinstance(ffield.widget, forms.CheckboxInput) or isinstance(
                ffield.widget, forms.RadioSelect
            ):
                self.styled_fields.remove(field)

        # define as classes css para todos
        for field in self.styled_fields:
            self.fields[field].widget.attrs["class"] = self.field_class


class Form(FieldStyledMixin, forms.Form):
    pass


class ModelForm(FieldStyledMixin, forms.ModelForm):
    pass


class ModelFormMixIn:
    def get_form_class(self):
        """
        Returns the form class to use in this view.
        """
        if self.fields is not None and self.form_class:
            raise ImproperlyConfigured(
                "Specifying both 'fields' and 'form_class' is not permitted."
            )
        if self.form_class:
            return self.form_class
        else:
            if self.model is not None:
                # If a model has been explicitly provided, use it
                model = self.model
            elif hasattr(self, "object") and self.object is not None:
                # If this view is operating on a single object, use
                # the class of that object
                model = self.object.__class__
            else:
                # Try to get a queryset and extract the model class
                # from that
                model = self.get_queryset().model

            if self.fields is None:
                raise ImproperlyConfigured(
                    f"Using ModelFormMixin (base class of {self.__class__.__name__}) without "
                    f"the 'fields' attribute is prohibited."
                )

            return model_forms.modelform_factory(
                model, fields=self.fields, form=ModelForm
            )
