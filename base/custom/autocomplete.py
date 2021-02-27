import operator
from functools import reduce

from ajax_select import LookupChannel
from ajax_select.registry import registry
from django.apps import apps
from django.db import models

from base.custom import field


def auto_complete(model, field_path, fields, title=None):

    if isinstance(model, str):
        model = apps.get_model(model)

    class AutoComplete(LookupChannel):
        @classmethod
        def get_channel_name(cls):
            return model.__name__ + "".join(fields)

        def get_fields_filter(self):
            result = []
            for f in fields:
                f_obj = field.resolve_type(self.model, f)
                filter_name = f
                if isinstance(f_obj, (models.CharField, models.TextField)):
                    filter_name += "__unaccent"
                result.append(filter_name + "__icontains")
            return result

        def _construct_autocomplete_query(self, q):
            def get_q(field_name):
                return reduce(
                    operator.and_, [models.Q(**{field_name: p}) for p in q.split()]
                )

            return reduce(operator.or_, [get_q(f) for f in self.get_fields_filter()])

        def get_query(self, q, request):
            q = q.strip()
            if q:
                return self.model.objects.filter(
                    self._construct_autocomplete_query(q)
                ).distinct()[:10]
            return self.model.objects.none()

        def get_objects(self, ids):
            return super().get_objects([int(aid) for aid in ids])

        def check_auth(self, request):
            return request.user.is_authenticated

    AutoComplete.model = model
    AutoComplete.fields = fields
    AutoComplete.field_path = field_path
    AutoComplete.title = title

    registry.register({AutoComplete.get_channel_name(): AutoComplete})
    return AutoComplete
