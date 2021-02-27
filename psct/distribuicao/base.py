import abc
import math
import random

from django.contrib.auth.models import Group
from django.db import transaction

from psct import itertools


class DistribuidorItemGrupo(metaclass=abc.ABCMeta):
    mailbox_class = None
    item_model = None
    group_class = Group
    distribuidorusuario_class = None

    def __init__(self, fase, coluna, map):
        self.fase = fase
        self.coluna = coluna
        self.map = map

    def get_mailbox(self, group):
        return self.mailbox_class.objects.get_or_create(
            **self.get_mailbox_kwargs(group)
        )[0]

    def get_items(self, filter_value):
        return self.item_model.objects.filter(
            **{self.coluna.query_string: filter_value, "fase": self.fase}
        )

    @abc.abstractmethod
    def get_mailbox_kwargs(self, group):
        return {}

    @abc.abstractmethod
    def get_mailbox_collection(self, mailbox):
        pass

    def adicionar_items_mailbox(self, mailbox, items):
        collection = self.get_mailbox_collection(mailbox)
        collection.add(*items)

    def get_group(self, group_id):
        return self.group_class.objects.get(id=group_id)

    def executar(self):
        with transaction.atomic():
            for filter_value, group_id in self.map.items():
                group = self.get_group(group_id)
                itens = self.get_items(filter_value)
                mailbox = self.get_mailbox(group)
                self.adicionar_items_mailbox(mailbox, itens)
                distribuidor_usuario = self.distribuidorusuario_class(superbox=mailbox)
                distribuidor_usuario.executar()


class DistribuidorItemUsuario(metaclass=abc.ABCMeta):
    userbox_class = None

    def __init__(self, superbox):
        self.superbox = superbox
        self.items = list(self.get_items(superbox))
        self.todos_usuarios = list(superbox.grupo.user_set.all())
        self.total_subgrupos = math.ceil(
            len(self.todos_usuarios) / self.get_tamanho_subgrupo()
        )
        self.embaralhar()

    @abc.abstractmethod
    def get_items(self, superbox):
        return []

    def embaralhar(self):
        random.shuffle(self.items)
        random.shuffle(self.todos_usuarios)

    @abc.abstractmethod
    def get_tamanho_subgrupo(self):
        return 1

    def get_subgrupos(self):
        return list(
            itertools.grouper_cycle(
                self.todos_usuarios, self.total_subgrupos, self.get_tamanho_subgrupo()
            )
        )

    def get_userbox(self, usuario):
        return self.userbox_class.objects.get_or_create(
            **self.get_userbox_kwargs(usuario)
        )[0]

    @abc.abstractmethod
    def get_userbox_kwargs(self, usuario):
        return {}

    @abc.abstractmethod
    def get_userbox_collection(self, userbox):
        return userbox

    def adicionar_item_usuario(self, usuario, item):
        userbox = self.get_userbox(usuario)
        collection = self.get_userbox_collection(userbox)
        collection.add(item)

    def adicionar_item_subgrupo(self, item, subgrupo):
        for usuario in subgrupo:
            self.adicionar_item_usuario(usuario, item)

    def adicionar_items_subgrupo(self, items, subgrupo):
        for item in items:
            self.adicionar_item_subgrupo(item, subgrupo)

    @property
    def items_por_subgrupo(self):
        return itertools.take(self.items, self.total_subgrupos)

    def executar(self):
        for items, subgrupo in zip(self.items_por_subgrupo, self.get_subgrupos()):
            self.adicionar_items_subgrupo(items, subgrupo)


class RedistribuirItemUsuario(metaclass=abc.ABCMeta):
    userbox_class = None

    def __init__(self, source, target, size):
        self.source = source
        self.target = target
        self.size = size

    def get_userbox(self, usuario):
        return self.userbox_class.objects.get_or_create(
            **self.get_userbox_kwargs(usuario)
        )[0]

    @abc.abstractmethod
    def get_userbox_kwargs(self, usuario):
        raise NotImplemented

    @abc.abstractmethod
    def get_userbox_collection(self, userbox):
        raise NotImplemented

    def get_source_itens(self, source):
        userbox = self.get_userbox(source)
        return self.get_userbox_collection(userbox)

    def get_size(self):
        return self.size

    def executar(self):
        itens = list(self.get_source_itens(self.source)[: self.get_size()])
        sourcebox = self.get_userbox(self.source)
        targetbox = self.get_userbox(self.target)
        collection = self.get_userbox_collection(targetbox)
        collection_source = self.get_userbox_collection(sourcebox)
        for item in itens:
            collection.add(item)
            collection_source.remove(item)
        return len(itens)
