# myproject/celery.py

import os

from celery import Celery
# from celery.schedules import crontab  # Import crontab for scheduling

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# app = Celery('abs_core')
# REDIS_URL="redis://redis-ighxwp.serverless.usw2.cache.amazonaws.com:6379"
REDIS_URL = "redis://redis:6379"
app = Celery("core", broker=REDIS_URL, backend=REDIS_URL)


# Load task modules from all registered Django app configs.
app.config_from_object("django.conf:settings", namespace="CELERY")


app.conf.broker_connection_retry_on_startup = True

app.conf.broker_connection_max_retries = 5
app.conf.broker_connection_timeout = 5


# Define periodic tasks
app.conf.beat_schedule = {}
