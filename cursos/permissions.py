from ifpb_django_permissions.perms import Group, Model


class CoordenadoresdeCursosdosCampi(Group):
    name = "Coordenadores de Cursos dos Campi"
    app = "cursos"
    permissions = [
        Model("cursos.atoregulatorio"),
        Model("cursos.cursonocampus", mode="c"),
        Model("cursos.disciplina", mode="ac"),
        Model("cursos.disciplinacurso"),
        Model("cursos.docente", mode="c"),
        Model("cursos.docenteexterno", mode="acd"),
        Model("cursos.documento"),
        Model("cursos.vagacurso"),
    ]


class AdministradoresSistemicosdeCursosdePosGraduacao(Group):
    name = "Administradores Sistêmicos de Cursos de Pós-Graduação"
    app = "cursos"
    permissions = [
        Model("cursos.atoregulatorio"),
        Model("cursos.curso", mode="ac"),
        Model("cursos.cursonocampus", mode="ac"),
        Model("cursos.disciplinacurso"),
        Model("cursos.disciplina", mode="ac"),
        Model("cursos.docente", mode="c"),
        Model("cursos.docenteexterno", mode="acd"),
        Model("cursos.documento"),
        Model("cursos.tipodocumento", mode="ac"),
        Model("cursos.vagacurso"),
    ]


class DiretoresdeEnsino(Group):
    name = "Diretores de Ensino"
    app = "cursos"
    permissions = [
        Model("cursos.atoregulatorio"),
        Model("cursos.campus", mode="c"),
        Model("cursos.cursonocampus", mode="ac"),
        Model("cursos.disciplinacurso"),
        Model("cursos.docente", mode="c"),
        Model("cursos.docenteexterno", mode="acd"),
        Model("cursos.documento"),
        Model("cursos.vagacurso"),
    ]


class AdministradoresSistemicosdeCursos(Group):
    name = "Administradores Sistêmicos de Cursos"
    app = "cursos"
    permissions = [
        Model("cursos.atoregulatorio"),
        Model("cursos.campus", mode="ac"),
        Model("cursos.cidade", mode="ac"),
        Model("cursos.curso", mode="ac"),
        Model("cursos.cursonocampus", mode="ac"),
        Model("cursos.disciplina", mode="ac"),
        Model("cursos.disciplinacurso"),
        Model("cursos.docenteexterno", mode="acd"),
        Model("cursos.docente", mode="c"),
        Model("cursos.documento"),
        Model("cursos.ies", mode="c"),
        Model("cursos.polo", mode="ac"),
        Model("cursos.tipoatoregulatorio", mode="ac"),
        Model("cursos.tipodocumento", mode="ac"),
        Model("cursos.vagacurso"),
    ]
