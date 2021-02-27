import operator
from datetime import date, datetime
from functools import reduce

from django.db import models
from django.db.models import Q

from cursos.models import CursoNoCampus
from editais.models import Edital
from noticias.models import Noticia
from processoseletivo.models import ProcessoSeletivo


class SearchMixin:
    def search(self, search_terms, fields=None):
        terms = [term.strip() for term in search_terms.split()]
        q_objects = []
        if terms:
            for term in terms:
                for field in self.fields_to_search:
                    clauses = dict()
                    clauses[field] = term
                    q_objects.append(Q(**{field: clauses[field]}))
            return self.filter(reduce(operator.or_, q_objects))
        else:
            return self.filter()


class NoticiaQuerySet(models.QuerySet, SearchMixin):
    fields_to_search = ["titulo__icontains", "corpo__icontains"]


class EditalQuerySet(models.QuerySet, SearchMixin):
    fields_to_search = ["nome__icontains", "descricao__icontains"]


class ProcessoSeletivoQuerySet(models.QuerySet, SearchMixin):
    fields_to_search = ["nome__icontains", "descricao__icontains", "sigla__icontains","id_icontais"]


class CursoQuerySet(models.QuerySet, SearchMixin):
    fields_to_search = [
        "curso__nome__icontains",
        "curso__perfil_unificado__icontains",
        "campus__nome__icontains",
    ]


class SearchCurso(CursoNoCampus):

    objects = CursoQuerySet.as_manager()

    class Meta:
        app_label = "base"
        proxy = True

    def titulo(self):
        return self

    def resumo(self):
        return self.curso.perfil_unificado

    def criado_por(self):
        return self.created_by()

    def atualizado_em(self):
        return self.last_edited_at()

    def criado_em(self):
        return self.created_at()

    def class_name(self):
        return super().curso._meta.verbose_name

    def assuntos(self):
        return self.palavras_chave


class SearchNoticia(Noticia):

    objects = NoticiaQuerySet.as_manager()

    class Meta:
        app_label = "base"
        proxy = True

    def titulo(self):
        return self.titulo

    def resumo(self):
        return self.alternative_text

    def criado_por(self):
        return self.responsavel

    def atualizado_em(self):
        return self.atualizacao

    def criado_em(self):
        return self.criacao

    def class_name(self):
        return super()._meta.verbose_name

    def assuntos(self):
        return self.palavras_chave


class SearchEdital(Edital):

    objects = EditalQuerySet.as_manager()

    class Meta:
        app_label = "base"
        proxy = True

    def titulo(self):
        return self.nome

    def resumo(self):
        return self.descricao

    def criado_por(self):
        return self.setor_responsavel

    def atualizado_em(self):
        ultima_retificacao = self.retificacoes.last()
        data = (
            ultima_retificacao.data_publicacao
            if ultima_retificacao
            else self.data_publicacao
        )
        return (
            datetime.fromordinal(data.toordinal()) if isinstance(data, date) else data
        )

    def criado_em(self):
        data = self.data_publicacao
        if isinstance(data, date):
            return datetime.fromordinal(data.toordinal())
        else:
            return data

    def class_name(self):
        return super()._meta.verbose_name

    def assuntos(self):
        return list()


class SearchProcessoSeletivo(ProcessoSeletivo):

    objects = ProcessoSeletivoQuerySet.as_manager()

    class Meta:
        app_label = "base"
        proxy = True

    def titulo(self):
        return self.nome

    def resumo(self):
        return ""

    def criado_por(self):
        return self.created_by()

    def atualizado_em(self):
        data = self.last_edited_at()
        return (
            datetime.fromordinal(data.toordinal()) if isinstance(data, date) else data
        )

    def criado_em(self):
        data = self.created_at()
        if isinstance(data, date):
            return datetime.fromordinal(data.toordinal())
        else:
            return self.created_at()

    def class_name(self):
        return super()._meta.verbose_name

    def assuntos(self):
        return list()
    def palavra_chave(self):
        return self.palavra_chave
class ModelProcessoseletivo(ProcessoSeletivo):
    objects = ProcessoSeletivoQuerySet.as_manager()
    def modelprocesso(self):
        return self.models.ProcessoSeletivo
