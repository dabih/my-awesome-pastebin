from django.db import models

import nanoid


def generate_nanoid():
    return nanoid.generate()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name_plural = "categories"


class Paste(models.Model):
    uid = models.CharField(max_length=21, unique=True, default=generate_nanoid)
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    expiration_datetime = models.DateTimeField(null=True, blank=True)
    password = models.CharField(max_length=100, null=True, blank=True)
    burn_after_read = models.BooleanField(default=False)
    syntax = models.CharField(max_length=50, default="plain")
    raw_data = models.TextField()
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class VisitCount(models.Model):
    paste = models.ForeignKey(Paste, on_delete=models.CASCADE, unique=True)
    count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)


class Report(models.Model):
    class ReportType(models.TextChoices):
        TOP_PASTES = "top_pastes", "Top-10 Popular Pastes"
        DAILY_FREQUENCY = "daily_frequency", "Daily Paste Frequency"

    type = models.CharField(max_length=50, choices=ReportType.choices)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.get_type_display()} — {self.created_at:%Y-%m-%d %H:%M}"

    class Meta:
        ordering = ["-created_at"]
