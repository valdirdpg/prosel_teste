import re


def remove_simbolos_cpf(cpf):
    return re.sub(r"[-\.]", "", cpf)
