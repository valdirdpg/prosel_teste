from ifpb_django_permissions.perms import Group, Model


class Candidatos(Group):
    name = "Candidatos"
    app = "candidatos"
    permissions = [Model("candidatos.caracterizacao", mode="c")]


class AdministradoresdeCandidatos(Group):
    name = "Administradores de Candidatos"
    app = "candidatos"
    permissions = [
        Model("candidatos.beneficiogovernofederal"),
        Model("candidatos.caracterizacao"),
        Model("candidatos.companhiadomiciliar"),
        Model("candidatos.comunicadocandidato"),
        Model("candidatos.contribuinterendafamiliar"),
        Model("candidatos.estadocivil"),
        Model("candidatos.idioma"),
        Model("candidatos.meiotransporte"),
        Model("candidatos.necessidadeespecial"),
        Model("candidatos.nivelescolaridade"),
        Model("candidatos.raca"),
        Model("candidatos.razaoafastamentoeducacional"),
        Model("candidatos.rendimentocaracterizacao"),
        Model("candidatos.situacaotrabalho"),
        Model("candidatos.tipoacessointernet"),
        Model("candidatos.tipoarearesidencial"),
        Model("candidatos.tipoemprego"),
        Model("candidatos.tipoescola"),
        Model("candidatos.tipoimovelresidencial"),
        Model("candidatos.tiposervicosaude"),
    ]
