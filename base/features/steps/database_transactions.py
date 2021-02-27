import datetime

from behave import when, then

from base.models import PessoaFisica


@when(u"I save the object")
def save_object(context):
    data = {
        "nome": u"João Ninguém",
        "cpf": "060.464.214-89",
        "nascimento": datetime.date(2000, 1, 1),
        "nome_responsavel": "Nome da Mãe",
        "parentesco_responsavel": "PAIS",
        "sexo": "M",
        "nacionalidade": "BRASILEIRA",
        "naturalidade": "Cidade de Nascimento",
        "naturalidade_uf": "PB",
        "logradouro": "Nome da Rua",
        "numero_endereco": 1,
        "bairro": "Nome do Bairro",
        "municipio": "Nome da cidade onde mora",
        "uf": "PB",
        "cep": "58.000-000",
        "tipo_zona_residencial": "URBANA",
        "telefone": "(32) 13213-2132",
        "email": "email@ifpb.edu.br",
    }
    PessoaFisica.objects.create(**data)


@then(u"I should only have one object")
def should_have_only_one_object(context):
    assert 1 == PessoaFisica.objects.count()
