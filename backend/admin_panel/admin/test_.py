from datetime import timedelta

import pytest
from django.utils import timezone

from pastes.models import Category, Paste, Report, VisitCount
from pastes.tasks import delete_expired_pastes, generate_daily_frequency_report, generate_top_pastes_report


@pytest.fixture
def category(db):
    return Category.objects.create(name="Python")


@pytest.fixture
def paste(category):
    return Paste.objects.create(title="Hello", category=category, raw_data="print('hi')", created_at=timezone.now())


@pytest.fixture
def paste_with_visits(paste):
    VisitCount.objects.create(paste=paste, count=42, last_updated=timezone.now())
    return paste


@pytest.mark.django_db
def test_category_str(category):
    assert str(category) == "Python"


@pytest.mark.django_db
def test_paste_uid_generated(paste):
    assert paste.uid
    assert len(paste.uid) == 21


@pytest.mark.django_db
def test_paste_defaults(paste):
    assert paste.deleted is False
    assert paste.burn_after_read is False
    assert paste.syntax == "plain"
    assert paste.password is None
    assert paste.expiration_datetime is None


@pytest.mark.django_db
def test_paste_str(paste):
    assert str(paste) == "Hello"


@pytest.mark.django_db
def test_visit_count_creation(paste):
    vc = VisitCount.objects.create(paste=paste, count=5, last_updated=timezone.now())
    assert vc.count == 5
    assert vc.paste == paste


@pytest.mark.django_db
def test_report_str():
    cat = Category.objects.create(name="Test")
    paste = Paste.objects.create(title="T", category=cat, raw_data="x", created_at=timezone.now())
    VisitCount.objects.create(paste=paste, count=1, last_updated=timezone.now())
    generate_top_pastes_report()
    report = Report.objects.latest("created_at")
    assert "Top-10" in str(report)


@pytest.mark.django_db
def test_delete_expired_pastes_marks_deleted(category):
    expired = Paste.objects.create(
        title="Old",
        category=category,
        raw_data="data",
        created_at=timezone.now(),
        expiration_datetime=timezone.now() - timedelta(hours=1),
    )
    delete_expired_pastes()
    expired.refresh_from_db()
    assert expired.deleted is True


@pytest.mark.django_db
def test_delete_expired_pastes_keeps_valid(category):
    valid = Paste.objects.create(
        title="Fresh",
        category=category,
        raw_data="data",
        created_at=timezone.now(),
        expiration_datetime=timezone.now() + timedelta(hours=1),
    )
    delete_expired_pastes()
    valid.refresh_from_db()
    assert valid.deleted is False


@pytest.mark.django_db
def test_delete_expired_pastes_skips_no_expiry(category):
    permanent = Paste.objects.create(
        title="Forever",
        category=category,
        raw_data="data",
        created_at=timezone.now(),
    )
    delete_expired_pastes()
    permanent.refresh_from_db()
    assert permanent.deleted is False


@pytest.mark.django_db
def test_generate_top_pastes_report(paste_with_visits):
    generate_top_pastes_report()
    report = Report.objects.latest("created_at")
    assert report.type == Report.ReportType.TOP_PASTES
    assert len(report.data) == 1
    assert report.data[0]["title"] == "Hello"
    assert report.data[0]["count"] == 42


@pytest.mark.django_db
def test_generate_top_pastes_report_excludes_deleted(category):
    deleted_paste = Paste.objects.create(
        title="Deleted",
        category=category,
        raw_data="x",
        created_at=timezone.now(),
        deleted=True,
    )
    VisitCount.objects.create(paste=deleted_paste, count=999, last_updated=timezone.now())
    generate_top_pastes_report()
    report = Report.objects.latest("created_at")
    assert all(item["title"] != "Deleted" for item in report.data)


@pytest.mark.django_db
def test_generate_daily_frequency_report(paste):
    generate_daily_frequency_report()
    report = Report.objects.latest("created_at")
    assert report.type == Report.ReportType.DAILY_FREQUENCY
    assert len(report.data) == 1
    assert report.data[0]["count"] == 1


@pytest.mark.django_db
def test_generate_daily_frequency_report_excludes_deleted(category):
    Paste.objects.create(title="Active", category=category, raw_data="x", created_at=timezone.now())
    Paste.objects.create(title="Deleted", category=category, raw_data="x", created_at=timezone.now(), deleted=True)
    generate_daily_frequency_report()
    report = Report.objects.latest("created_at")
    assert report.data[0]["count"] == 1
