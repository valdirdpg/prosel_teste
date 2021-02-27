from django import forms

from psct.models import CriterioAlternativa, RespostaCriterio, RespostaModelo


class ResponderQuestionarioForm(forms.Form):
    def __init__(self, modelo, candidato, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modelo = modelo
        self.edital = modelo.edital
        self.candidato = candidato
        self.resposta_modelo, created = RespostaModelo.objects.get_or_create(
            modelo=self.modelo, candidato=self.candidato
        )
        questions = modelo.itens_avaliados.all()

        for i, question in enumerate(questions):
            opcoes = CriterioAlternativa.objects.filter(criterio=question)
            initial = RespostaCriterio.objects.filter(
                resposta_modelo=self.resposta_modelo,
                criterio_alternativa_selecionada__in=opcoes,
            ).values_list("criterio_alternativa_selecionada_id", flat=True)
            choices = [
                (c.id, c.descricao_alternativa)
                for c in CriterioAlternativa.objects.filter(criterio=question)
            ]
            if question.multipla_escolha:
                self.fields[f"questao_id_{question.pk}"] = forms.MultipleChoiceField(
                    choices=choices,
                    label=question,
                    widget=forms.CheckboxSelectMultiple,
                    initial=list(initial),
                )
            else:
                self.fields[f"questao_id_{question.pk}"] = forms.ChoiceField(
                    choices=choices, widget=forms.RadioSelect, label=question
                )
                if initial:
                    self.fields[f"questao_id_{question.pk}"].initial = initial[0]

    def save(self):
        data = self.cleaned_data
        RespostaCriterio.objects.filter(resposta_modelo=self.resposta_modelo).delete()
        for resposta in data.values():
            if isinstance(resposta, str):
                alternativa_selecionada = CriterioAlternativa.objects.get(id=resposta)
                RespostaCriterio.objects.create(
                    resposta_modelo=self.resposta_modelo,
                    criterio_alternativa_selecionada=alternativa_selecionada,
                )
            elif isinstance(resposta, list):
                alternativas = CriterioAlternativa.objects.filter(id__in=resposta)
                for alternativa in alternativas.all():
                    RespostaCriterio.objects.create(
                        resposta_modelo=self.resposta_modelo,
                        criterio_alternativa_selecionada=alternativa,
                    )
