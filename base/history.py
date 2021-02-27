from django.contrib.admin.models import ADDITION
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType


class HistoryMixin:
    def get_history(self):
        content_type = ContentType.objects.get_for_model(self)
        return LogEntry.objects.filter(object_id=self.pk, content_type=content_type)

    def last_edited_at(self):
        history = list(self.get_history()[:1])
        return history[0].action_time if history else None

    def last_edited_by(self):
        history = list(self.get_history()[:1])
        return history[0].user if history else None

    def created_at(self):
        history = self.get_history().filter(action_flag=ADDITION)
        return history[0].action_time if history else self.last_edited_at()

    def created_by(self):
        history = self.get_history().filter(action_flag=ADDITION)
        return history[0].user if history else self.last_edited_by()

    def user_actions(self, user):
        return self.get_history().filter(user=user)
