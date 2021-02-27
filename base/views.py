from datetime import datetime
from itertools import chain
from operator import attrgetter
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render
from django.views import generic
from ifpb_django_permissions.perms import in_any_groups
from base.search import SearchCurso, SearchEdital, SearchNoticia, SearchProcessoSeletivo
from candidatos.permissions import Candidatos
from noticias.models import Assunto, Noticia
from psct.permissions import CandidatosPSCT

#class ProcessosView(generic.TemplateView):
#    template_name = "processoseletivo/index2.html"

class BaseView(generic.TemplateView):
    template_name = "base/index.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if Noticia.objects.publicadas().destaques().exists():
            qs_destaques = Noticia.objects.publicadas().destaques()[:5]
        else:
            qs_destaques = Noticia.objects.publicadas()[:3]
        id_destaques = list(qs_destaques.values_list("id", flat=True))
        context["destaques"] = qs_destaques
        qs_ultimas = Noticia.objects.publicadas().exclude(id__in=id_destaques)[:3]
        id_ultimas = list(qs_ultimas.values_list("id", flat=True))
        context["ultimas"] = qs_ultimas
        grupos = list()
        assuntos = Assunto.objects.pagina_inicial()
        assuntos = list(assuntos)
        assuntos.sort(key=attrgetter("noticia_mais_recente.criacao"), reverse=True)
        for assunto in assuntos:
            grupos.append(
                (
                    assunto,
                    assunto.noticia_set.publicadas().exclude(
                        id__in=id_ultimas + id_destaques
                    )[: assunto.quantidade],
                )
            )
        context["grupos"] = grupos
        return context
    def get_template_names(self):
        if in_any_groups(self.request.user, [Candidatos, CandidatosPSCT]):
            return ["base/index_candidato.html"]
        return super().get_template_names()
class AcessibilidadeView(generic.TemplateView):
    template_name = "base/acessibilidade.html"
class SearchView(generic.TemplateView):
    template_name = "base/search.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", None)
        if q:
            context["q"] = q
            resultados_noticias = SearchNoticia.objects.search(q)
            resultados_editais = SearchEdital.objects.search(q)
            resultados_processo_seletivo = SearchProcessoSeletivo.objects.search(q)
            resultados_cursos = SearchCurso.objects.search(q)
            resultados = list(
                chain(
                    resultados_noticias,
                    resultados_editais,
                    resultados_processo_seletivo,
                    resultados_cursos,
                )
            )
            resultados.sort(key=lambda x: x.criado_em() or datetime(1900, 1, 1))
            resultados.reverse()
            paginator = Paginator(resultados, 5)
            page = self.request.GET.get("page")
            try:
                context["resultados"] = paginator.page(page)
            except PageNotAnInteger:
                context["resultados"] = paginator.page(1)
            except EmptyPage:
                context["resultados"] = paginator.page(paginator.num_pages)
            if context["resultados"]:
                context["paginado"] = "S"
        return context
def permission_denied(request, exception):
    response = render(request, "base/403.html", {})
    response.status_code = 403
    return response
def page_not_found(request, exception):
    response = render(request, "base/404.html", {})
    response.status_code = 404
    return response
def server_error(request):
    response = render(request, "base/500.html", {})
    response.status_code = 500
    return response