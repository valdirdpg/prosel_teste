import os
import raven
from celery import Celery as DefaultCelery
from raven.contrib.celery import register_signal, register_logger_signal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portaldocandidato.settings")


class Celery(DefaultCelery):
    def on_configure(self):

        if os.environ.get("RAVEN_DSN") and not os.environ.get("CI_BUILD_REF"):
            client = raven.Client(os.environ["RAVEN_DSN"])

            # register a custom filter to filter out duplicate logs
            register_logger_signal(client)

            # hook into the Celery error handler
            register_signal(client)


app = Celery("portaldocandidato")

app.config_from_object("django.conf:settings")


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
