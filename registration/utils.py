def is_user_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


def is_admin_sistemico_cursos(user):
    return is_user_in_group(user, "Administradores Sistêmicos de Cursos")


def is_admin_sistemico_cursos_pos(user):
    return is_user_in_group(
        user, "Administradores Sistêmicos de Cursos de Pós-Graduação"
    )


def is_diretor_ensino(user):
    return is_user_in_group(user, "Diretores de Ensino")


def is_administrador_cursos_campus(user):
    return is_user_in_group(user, "Administradores de Cursos nos Campi")


def is_coordenador_curso(user):
    return is_user_in_group(user, "Coordenadores de Cursos dos Campi")
