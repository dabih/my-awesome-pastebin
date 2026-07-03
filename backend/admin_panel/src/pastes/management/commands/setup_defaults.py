import os

# from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Sets up defaults"

    def handle(self, *args, **options):
        self.setup_superuser()
        self.setup_celery_task()

    def setup_superuser(self):
        user = get_user_model()
        username = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
        email = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@example.com")
        password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin")

        if not user.objects.filter(username=username).exists():
            user.objects.create_superuser(username=username, email=email, password=password, is_staff=True, is_superuser=True)
            self.stdout.write(self.style.SUCCESS(f"Successfully created superuser: {username}"))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser {username} already exists, skipping creation"))

    def setup_celery_task(self):
        tasks = [
            {
                "name": "delete_expired_pastes",
                "task": "pastes.tasks.delete_expired_pastes",
                "schedule": {"minute": "*/5", "hour": "*", "day_of_week": "*", "day_of_month": "*", "month_of_year": "*"},
            },
            {
                "name": "generate_top_pastes_report",
                "task": "pastes.tasks.generate_top_pastes_report",
                "schedule": {"minute": "0", "hour": "0", "day_of_week": "*", "day_of_month": "*", "month_of_year": "*"},
            },
            {
                "name": "generate_daily_frequency_report",
                "task": "pastes.tasks.generate_daily_frequency_report",
                "schedule": {"minute": "0", "hour": "0", "day_of_week": "*", "day_of_month": "*", "month_of_year": "*"},
            },
        ]
        for task_config in tasks:
            task_name = task_config["name"]
            if not PeriodicTask.objects.filter(name=task_name).exists():
                schedule, _ = CrontabSchedule.objects.get_or_create(**task_config["schedule"])
                PeriodicTask.objects.create(
                    name=task_name,
                    task=task_config["task"],
                    crontab=schedule,
                    enabled=True,
                )
                self.stdout.write(self.style.SUCCESS(f"Successfully created periodic task: {task_name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Periodic task {task_name} already exists, skipping creation"))
