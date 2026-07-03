import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "admin.settings")

app = Celery("admin")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.timezone = "UTC"

app.autodiscover_tasks()
