# celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iki.settings')

app = Celery('iki')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related config keys should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Celery Beat settings
app.conf.beat_schedule = {
    'delete-expired-statuses': {
        'task': 'api.tasks.delete_expired_statuses',
        'schedule': 1200.0,  # Every minute
    },
}

