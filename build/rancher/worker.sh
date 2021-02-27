#!/usr/bin/env bash
celery -A portaldocandidato worker -l info --autoscale=10,4

