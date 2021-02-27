from django import forms

from base.forms import Form
from psct.render import driver
from psct.render import register


class FileFormatForm(Form):
    render = forms.ChoiceField(
        label="Escolha o tipo de arquivo que deseja gerar", choices=[]
    )
    filetype = forms.ChoiceField(label="Escolha a extensão do arquivo", choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["render"].choices = register.get_choices()
        self.fields["filetype"].choices = driver.get_choices()
