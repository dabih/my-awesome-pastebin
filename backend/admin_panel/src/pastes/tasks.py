from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from celery import shared_task

from .models import Paste, Report, VisitCount


@shared_task
def delete_expired_pastes():
    now = timezone.now()
    expired_pastes = Paste.objects.filter(expiration_datetime__lte=now, deleted=False)
    expired_pastes.update(deleted=True)


@shared_task
def generate_top_pastes_report():
    top = VisitCount.objects.select_related("paste").filter(paste__deleted=False).order_by("-count")[:10]
    data = [{"uid": vc.paste.uid, "title": vc.paste.title, "count": vc.count} for vc in top]
    Report.objects.create(type=Report.ReportType.TOP_PASTES, data=data)


@shared_task
def generate_daily_frequency_report():
    rows = (
        Paste.objects.filter(deleted=False)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("-date")[:30]
    )
    data = [{"date": str(row["date"]), "count": row["count"]} for row in rows]
    Report.objects.create(type=Report.ReportType.DAILY_FREQUENCY, data=data)
