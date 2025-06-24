import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django_celery_beat.models import PeriodicTask, CrontabSchedule

class Command(BaseCommand):
    help = "Sets up defaults"

    def handle(self, *args, **options):
        self.setup_superuser()
        self.setup_celery_task()


    def setup_superuser(self):
        username = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
        email = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@example.com")
        password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin")

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully created superuser: {username}"))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser {username} already exists, skipping creation"))


    def setup_celery_task(self):
        task_name = "delete_expired_pastes"
        if not PeriodicTask.objects.filter(name=task_name).exists():
            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute="*/5",
                hour="*",
                day_of_week="*",
                day_of_month="*",
                month_of_year="*",
            )
            PeriodicTask.objects.create(
                name=task_name,
                task="pastes.tasks.delete_expired_pastes",
                crontab=schedule,
                enabled=True,
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully created periodic task: {task_name}"))
        else:
            self.stdout.write(self.style.WARNING(f"Periodic task {task_name} already exists, skipping creation"))
