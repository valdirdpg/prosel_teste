from ifpb_django_permissions.perms import Group, Model


class GerentesSetoriaisdeEditais(Group):
    name = "Gerentes Setoriais de Editais"
    app = "editais"
    permissions = [
        Model("editais.cronograma"),
        Model("editais.documento"),
        Model("editais.edital", mode="ac"),
        Model("editais.nivelselecao"),
        Model("editais.periodoselecao"),
    ]


class AdministradoresSistemicosdeEditais(Group):
    name = "Administradores Sistêmicos de Editais"
    app = "editais"
    permissions = [
        Model("editais.cronograma"),
        Model("editais.documento"),
        Model("editais.edital"),
        Model("editais.nivelselecao"),
        Model("editais.periodoconvocacao"),
        Model("editais.periodoselecao"),
        Model("processoseletivo.edicao", mode="ac"),
        Model("processoseletivo.processoseletivo", mode="ac"),
    ]
