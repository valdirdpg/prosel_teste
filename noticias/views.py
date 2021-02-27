from django.shortcuts import get_object_or_404
from django.views import generic

from . import models


class NoticiasPublicadas:
    queryset = models.Noticia.objects.publicadas()


class NoticiasListView(NoticiasPublicadas, generic.ListView):
    template_name = "noticias/noticia_list.html"
    paginate_by = 10
    ordering = ["-atualizacao"]


class NoticiaDetailView(NoticiasPublicadas, generic.DetailView):
    template_name = "noticias/detalhe_noticia.html"
    context_object_name = "noticia"


class NoticiasAssuntoListView(NoticiasListView):
    def get_assunto(self):
        self.assunto = None
        if not self.assunto and "slug" in self.kwargs:
            self.assunto = get_object_or_404(models.Assunto, slug=self.kwargs["slug"])
        return self.assunto

    def get_queryset(self):
        return super().get_queryset().filter(assunto=self.get_assunto())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assunto"] = self.assunto
        return context


class NoticiasPChaveListView(NoticiasListView):
    def get_palavra_chave(self):
        self.palavra_chave = None
        if not self.palavra_chave and "slug" in self.kwargs:
            self.palavra_chave = get_object_or_404(
                models.PalavrasChave, slug=self.kwargs["slug"]
            )
        return self.palavra_chave

    def get_queryset(self):
        return super().get_queryset().filter(palavras_chave=self.get_palavra_chave())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["palavra"] = self.palavra_chave
        return context
