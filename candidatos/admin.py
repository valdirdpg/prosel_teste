from django.contrib import admin

from . import models


@admin.register(
    models.NecessidadeEspecial,
    models.CompanhiaDomiciliar,
    models.TipoAreaResidencial,
    models.NivelEscolaridade,
)
class CandidatosBaseAdmin(admin.ModelAdmin):
    list_display = ("descricao",)


@admin.register(models.Raca, models.TipoEscola, models.EstadoCivil)
class CandidatosSuapBaseAdmin(CandidatosBaseAdmin):
    def get_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ["descricao", "valor_suap"]
        return ["descricao"]


@admin.register(models.ComunicadoCandidato)
class ComunicadoCandidatoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "assunto")
    fields = ("tipo", "assunto", "mensagem")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["tipo"]

        return []


@admin.register(models.Candidato)
class CandidatoAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf")
    search_fields = ("cpf", "nome", "email", "user__username")

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return "cpf", "nome", "user"
        return "cpf", "nome"

    def get_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ("cpf", "nome", "email")
        return super().get_fields(request, obj=obj)

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return (
                (
                    "Identificação",
                    {
                        "fields": (
                            ("cpf",),
                            ("nome",),
                            ("email",),
                            ("nome_social", "nascimento"),
                            ("profissao", "sexo", "tipo_sanguineo"),
                            ("nacionalidade", "naturalidade", "naturalidade_uf"),
                        )
                    },
                ),
                (
                    "Dados Familiares",
                    {
                        "fields": (
                            ("nome_mae", "nome_pai"),
                            (
                                "nome_responsavel",
                                "parentesco_responsavel",
                                "email_responsavel",
                            ),
                        )
                    },
                ),
                (
                    "Endereço e Contato",
                    {
                        "fields": (
                            ("logradouro", "numero_endereco"),
                            ("complemento_endereco", "bairro"),
                            ("municipio", "uf"),
                            ("cep", "tipo_zona_residencial"),
                            ("telefone", "telefone"),
                        )
                    },
                ),
                (
                    "Documentos",
                    {
                        "fields": (
                            ("rg", "data_expedicao"),
                            ("orgao_expeditor", "orgao_expeditor_uf"),
                            ("certidao_tipo", "certidao", "certidao_folha"),
                            ("certidao_livro", "certidao_data"),
                            ("numero_titulo_eleitor", "zona_titulo_eleitor"),
                            (
                                "secao_titulo_eleitor",
                                "data_emissao_titulo_eleitor",
                                "uf_titulo_eleitor",
                            ),
                        )
                    },
                ),
            )
        return super().get_fieldsets(request, obj=obj)


@admin.register(models.Caracterizacao)
class CaracterizacaoAdmin(admin.ModelAdmin):
    readonly_fields = ("candidato",)
    search_fields = ("candidato__cpf", "candidato__nome")
    fieldsets = (
        (
            "Dados Pessoais",
            {
                "fields": (
                    ("candidato"),
                    ("raca"),
                    ("possui_necessidade_especial", "necessidade_especial"),
                    ("estado_civil"),
                    ("qtd_filhos"),
                    ("tipo_servico_saude"),
                )
            },
        ),
        (
            "Dados Educacionais",
            {
                "fields": (
                    ("ensino_fundamental_conclusao", "ensino_medio_conclusao"),
                    ("escola_ensino_fundamental", "nome_escola_ensino_fundamental"),
                    ("escola_ensino_medio", "nome_escola_ensino_medio"),
                    (
                        "ficou_tempo_sem_estudar",
                        "tempo_sem_estudar",
                        "razao_ausencia_educacional",
                    ),
                    ("possui_conhecimento_idiomas", "idiomas_conhecidos"),
                    ("possui_conhecimento_informatica"),
                )
            },
        ),
        (
            "Situação Familiar e Socioeconômica",
            {
                "fields": (
                    ("trabalho_situacao"),
                    ("meio_transporte_utilizado"),
                    ("contribuintes_renda_familiar", "responsavel_financeiro"),
                    (
                        "responsavel_financeir_trabalho_situacao",
                        "responsavel_financeiro_nivel_escolaridade",
                    ),
                    ("estado_civil_pai", "pai_nivel_escolaridade", "pai_falecido"),
                    ("estado_civil_mae", "mae_nivel_escolaridade", "mae_falecida"),
                    ("renda_bruta_familiar"),
                    ("companhia_domiciliar", "qtd_pessoas_domicilio"),
                    ("tipo_imovel_residencial", "tipo_area_residencial"),
                    ("beneficiario_programa_social"),
                )
            },
        ),
        (
            "Acesso às Tecnologias da Informação e Comunicação",
            {
                "fields": (
                    ("frequencia_acesso_internet", "local_acesso_internet"),
                    (
                        "quantidade_computadores",
                        "quantidade_notebooks",
                        "quantidade_netbooks",
                        "quantidade_smartphones",
                    ),
                )
            },
        ),
    )
