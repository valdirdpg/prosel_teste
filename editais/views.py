from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views import generic

from editais import models
from editais.choices import CategoriaDocumentoChoices
from noticias.models import Noticia
from processoseletivo.models import ProcessoSeletivo


class EditalView(generic.TemplateView):

    template_name = "editais/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "processo" in self.request.GET:
            pk_processo = self.request.GET.get("processo")
            context["processo"] = get_object_or_404(ProcessoSeletivo, pk=pk_processo)
            editais_abertos = models.Edital.objects.filter(
                tipo="ABERTURA",
                edicao__processo_seletivo__id=pk_processo,
                publicado=True,
                encerrado=False,
            )
        else:
            editais_abertos = models.Edital.objects.filter(
                tipo="ABERTURA", publicado=True, encerrado=False
            )

        if editais_abertos.count() <= 10:
            context["editais_abertos"] = editais_abertos
        else:
            paginator = Paginator(editais_abertos.order_by("-id"), 10)
            page_n = self.request.GET.get("page", 1)
            try:
                page = paginator.page(page_n)
            except PageNotAnInteger:
                page = paginator.page(1)
            except EmptyPage:
                page = paginator.page(paginator.num_pages)
            context["editais_abertos"] = page
            context["paginado"] = "S"

        return context


class EditalArquivosView(generic.TemplateView):

    template_name = "editais/edital_arquivos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pk_edital = int(self.kwargs["pk_edital"])
        edital = get_object_or_404(models.Edital, pk=pk_edital)
        context["edital"] = edital

        categoria = self.kwargs["categoria"]
        if categoria == "PROVA":
            arquivos = models.Documento.objects.filter(
                Q(edital=edital, categoria=categoria)
                | Q(edital=edital, categoria="GABARITO")
                | Q(edital__retificado=edital, categoria=categoria)
                | Q(edital__retificado=edital, categoria="GABARITO")
            )
        elif categoria == "RESULTADO":
            arquivos = models.Documento.objects.filter(
                Q(edital=edital, categoria=categoria)
                | Q(edital=edital, categoria="RECURSO")
                | Q(edital__retificado=edital, categoria=categoria)
                | Q(edital__retificado=edital, categoria="RECURSO")
            )
        elif categoria in [c.name for c in CategoriaDocumentoChoices]:
            arquivos = models.Documento.objects.filter(
                Q(edital=edital, categoria=categoria)
                | Q(edital__retificado=edital, categoria=categoria)
            )
        else:
            raise Http404("CategoriaDocumento does not exist.")
        context["categoria_label"] = CategoriaDocumentoChoices.label(categoria)
        context["arquivos"] = arquivos

        return context


class EditaisEncerradosView(generic.TemplateView):

    template_name = "editais/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "processo" in self.request.GET:
            pk_processo = self.request.GET.get("processo")
            context["processo"] = get_object_or_404(ProcessoSeletivo, pk=pk_processo)
            editais_encerrados = models.Edital.objects.filter(
                tipo="ABERTURA",
                edicao__processo_seletivo__id=pk_processo,
                publicado=True,
                encerrado=True,
            )
        else:
            editais_encerrados = models.Edital.objects.filter(
                tipo="ABERTURA", publicado=True, encerrado=True
            )

        if editais_encerrados.count() <= 10:
            context["editais_encerrados"] = editais_encerrados
        else:
            paginator = Paginator(
                editais_encerrados.order_by("-id"), 10
            )  # Mostra 10 editais por página
            page_n = self.request.GET.get("page", 1)
            try:
                page = paginator.page(page_n)
            except PageNotAnInteger:
                page = paginator.page(1)
            except EmptyPage:
                page = paginator.page(paginator.num_pages)

            context["editais_encerrados"] = page
            context["paginado"] = "S"
        context["encerrados"] = True

        return context


class EditalDetailView(generic.TemplateView):

    template_name = "editais/edital_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pk_edital = int(self.kwargs["pk"])
        edital = get_object_or_404(models.Edital, pk=pk_edital)
        context["edital"] = edital

        noticias = Noticia.objects.filter(palavras_chave=edital.palavra_chave.pk)
        context["noticias"] = noticias

        return context
