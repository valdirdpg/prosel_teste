from ifpb_django_permissions.perms import Group, Model


class AdministradoresSistemicos(Group):
    name = "Administradores Sistêmicos"
    app = "base"
    permissions = [
        Model("cursos.atoregulatorio"),
        Model("cursos.campus", mode="ac"),
        Model("cursos.cidade", mode="ac"),
        Model("cursos.curso", mode="ac"),
        Model("cursos.cursonocampus", mode="ac"),
        Model("cursos.disciplina", mode="ac"),
        Model("cursos.disciplinacurso"),
        Model("cursos.docente", mode="ac"),
        Model("cursos.documento"),
        Model("cursos.historico"),
        Model("cursos.ies", mode="ac"),
        Model("cursos.polo", mode="ac"),
        Model("cursos.tipoatoregulatorio", mode="ac"),
        Model("cursos.tipodocumento", mode="ac"),
        Model("cursos.vagacurso"),
        Model("editais.cronograma"),
        Model("editais.documento"),
        Model("editais.edital", mode="ac"),
        Model("editais.nivelselecao"),
        Model("editais.periodoconvocacao"),
        Model("editais.periodoselecao"),
        Model("processoseletivo.edicao", mode="ac"),
        Model("processoseletivo.etapa", mode="ac"),
        Model("processoseletivo.modalidade", mode="ac"),
        Model("processoseletivo.processoseletivo", mode="ac"),
        Model("processoseletivo.transicaomodalidade", mode="ac"),
        Model("processoseletivo.transicaomodalidadepossivel", mode="ac"),
        Model("processoseletivo.vaga", mode="ac"),
    ]
