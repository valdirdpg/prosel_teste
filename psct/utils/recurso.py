from base.custom import permissions


def apenas_candidato(user):
    return (
        not permissions.user_in_groups(
            user, ["Homologador PSCT", "Avaliador PSCT", "Administradores PSCT"]
        )
    ) and not user.is_superuser
