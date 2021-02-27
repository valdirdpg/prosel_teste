from ifpb_django_permissions.perms import Group, Model


class AdministradoresdeChamadasporCampi(Group):
    name = "Administradores de Chamadas por Campi"
    app = "cursos"
    permissions = [
        Model("base.pessoafisica", mode="c"),
        Model("candidatos.candidato", mode="c"),
        Model("editais.periodoconvocacao", mode="ac"),
        Model("processoseletivo.analisedocumental"),
        Model("processoseletivo.avaliacaodocumental"),
        Model("processoseletivo.chamada", mode="c"),
        Model("processoseletivo.etapa", mode="ac"),
        Model("processoseletivo.recurso"),
    ]


class AdministradoresSistemicosdeChamadas(Group):
    name = "Administradores Sistêmicos de Chamadas"
    app = "cursos"
    permissions = [
        Model("editais.periodoconvocacao"),
        Model("processoseletivo.analisedocumental"),
        Model("processoseletivo.avaliacaodocumental"),
        Model("processoseletivo.chamada"),
        Model("processoseletivo.etapa", mode="ac"),
        Model("processoseletivo.recurso"),
        Model("processoseletivo.tipoanalise"),
        Model("processoseletivo.vaga", mode="ac"),
    ]


class Medicos(Group):
    name = "Médicos"
    app = "processoseletivo"

    permissions = [Model("processoseletivo.avaliacaodocumental", mode="a")]


class OperadorCaest(Group):
    name = "Operador CAEST"
    app = "processoseletivo"

    permissions = [Model("processoseletivo.avaliacaodocumental", mode="a")]
