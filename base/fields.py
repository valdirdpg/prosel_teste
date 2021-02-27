from django import forms
from django.core.exceptions import ValidationError
from snowpenguin.django.recaptcha2.fields import (
    ReCaptchaField,
)  # pylint: disable=import-error


class SafeReCaptchaField(ReCaptchaField):
    def clean(self, values):
        try:
            return super().clean(values)
        except KeyError:
            raise ValidationError("reCaptcha inválido. Tente de novo.")


class ModelChoiceCustomLabelField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        self.label_from_instance_func = kwargs.pop("label_from_instance_func")
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        return self.label_from_instance_func(obj)


class ModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def __init__(self, *args, **kwargs):
        self.label_from_instance_func = kwargs.pop("label_from_instance_func", None)
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        if self.label_from_instance_func:
            return self.label_from_instance_func(obj)
        return super().label_from_instance(obj)
