from ajax_select import LookupChannel
from ajax_select import register
from django.contrib.auth.models import User
from django.db.models import Q


@register("users")
class UserLookup(LookupChannel):

    model = User

    def get_query(self, q, request):
        return (
            self.model.objects.filter(
                Q(username__icontains=q)
                | Q(email__icontains=q)
                | Q(first_name__unaccent__icontains=q)
                | Q(last_name__unaccent__icontains=q)
            )
            .distinct()
            .order_by("first_name")[:10]
        )

    def format_item_display(self, item):
        return f"{item.get_full_name()} - {item.email} ({item.username})"

    def get_result(self, obj):
        return self.format_item_display(obj)

    def format_match(self, obj):
        return self.format_item_display(obj)
