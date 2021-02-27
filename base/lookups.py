from ajax_select import LookupChannel, register
from suaprest.django import SUAPDjangoClient as Client
from suaprest.exceptions import SuapError

from base.types import Servidor


@register("servidores")
class ServidorLookup(LookupChannel):
    def get_query(self, q, request):
        client = Client()
        try:
            return list(Servidor(s) for s in client.search_servidores(q))
        except SuapError:
            return []

    def format_item_display(self, item):
        return self.get_result(item)

    def get_objects(self, ids):
        if ids:
            client = Client()
            try:
                return list(Servidor(s) for s in client.get_servidores(ids))
            except SuapError:
                return []
        return []

    def get_result(self, obj):
        return str(obj)

    def format_match(self, obj):
        return self.format_item_display(obj)
