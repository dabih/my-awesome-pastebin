from django.contrib import admin
from .models import Category, Paste, VisitCount

class VisitCountInline(admin.TabularInline):
    model = VisitCount
    extra = 0

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')

@admin.register(Paste)
class PasteAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at', 'expiration_datetime', 'deleted')
    inlines = [VisitCountInline]

@admin.register(VisitCount)
class VisitCountAdmin(admin.ModelAdmin):
    list_display = ('paste', 'count', 'last_updated')
