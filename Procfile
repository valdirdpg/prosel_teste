web: gunicorn portaldocandidato.wsgi --log-file -
worker: celery -A portaldocandidato worker -l info --autoscale=10,4
