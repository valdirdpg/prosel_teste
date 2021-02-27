#!/usr/bin/env bash
python manage.py collectstatic --no-input
gunicorn portaldocandidato.wsgi -w 9 --timeout=1800 -b 0.0.0.0:8000