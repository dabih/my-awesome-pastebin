from celery import shared_task
from django.utils import timezone
from .models import Paste

@shared_task
def delete_expired_pastes():
    now = timezone.now()
    expired_pastes = Paste.objects.filter(
        expiration_datetime__lte=now, deleted=False
    )
    expired_pastes.update(deleted=True)
