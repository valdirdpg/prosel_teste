from django.core.exceptions import ValidationError


def senha_eh_valida(senha):
    if len(senha) < 8:
        raise ValidationError("A senha digitada possui menos de 8 caracteres.")
    contem_numero = False
    contem_letra = False
    for c in senha:
        contem_numero = contem_numero or c.isdigit()
        contem_letra = contem_letra or c.isalpha()
    if not contem_numero:
        raise ValidationError("A senha digitada não possui números.")
    if not contem_letra:
        raise ValidationError("A senha digitada não possui letras.")
