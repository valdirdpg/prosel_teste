from ifpb_django_permissions.perms import Group, Model


class CandidatosPSCT(Group):
    name = "Candidatos PSCT"
    app = "psct"


class HomologadorPSCT(Group):
    name = "Homologador PSCT"
    app = "psct"


class AvaliadorPSCT(Group):
    name = "Avaliador PSCT"
    app = "psct"


class AdministradoresPSCT(Group):
    name = "Administradores PSCT"
    app = "psct"
    permissions = [
        Model("processoseletivo.modalidade", mode="ac"),
        Model("processoseletivo.transicaomodalidade", mode="ac"),
        Model("processoseletivo.transicaomodalidadepossivel", mode="ac"),
        Model("psct.avaliacaoavaliador", mode="c"),
        Model(
            "psct.candidato",
            mode="c",
            codenames=["admin_can_change_email", "list_candidato"],
        ),
        Model("psct.colunaconsulta"),
        Model("psct.consulta"),
        Model("psct.consulta", mode="", codenames=["view_consulta"]),
        Model("psct.criterioalternativa", mode="ac"),
        Model("psct.criterioquestionario", mode="ac"),
        Model("psct.cursoedital", mode="c"),
        Model("psct.email"),
        Model("psct.email", mode="", codenames=["send_mail"]),
        Model("psct.faseajustepontuacao", mode="ac"),
        Model("psct.faseanalise", mode="ac"),
        Model("psct.faserecurso", mode="ac"),
        Model(
            "psct.inscricao",
            mode="",
            codenames=["view_inscricao", "list_inscricao", "add_list_inscritos"],
        ),
        Model("psct.justificativaindeferimento"),
        Model("psct.modalidade", mode="ac"),
        Model("psct.modalidadevagacursoedital", mode="ac"),
        Model("psct.modeloquestionario", mode="ac"),
        Model("psct.ordenacaoconsulta"),
        Model("psct.pareceravaliador", mode="c"),
        Model("psct.processoinscricao", mode="ac"),
        Model("psct.regrabase"),
        Model("psct.regraexclusao"),
        Model("psct.regrafiltro"),
        Model("psct.resultadopreliminar", mode="c"),
    ]


class ConfiguradorConsultaPSCT(Group):
    name = "Configurador Consulta - PSCT"
    app = "psct"
    permissions = [
        Model("psct.coluna"),
        Model("psct.colunaconsulta"),
        Model("psct.consulta", mode="", codenames=["view_consulta"]),
        Model("psct.consulta"),
        Model("psct.filtro"),
        Model("psct.ordenacaoconsulta"),
        Model("psct.regrabase"),
        Model("psct.regraexclusao"),
        Model("psct.regrafiltro"),
    ]


class ValidadordeComprovantesPSCT(Group):
    name = "Validador de Comprovantes PSCT"
    app = "psct"


class CCAPSCT(Group):
    name = "CCA PSCT"
    app = "psct"
