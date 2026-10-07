from django.contrib import admin
from .models import ExtractionJob, ExtractionRecord

@admin.register(ExtractionJob)
class ExtractionJobAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "status", "record_count", "created_at", "completed_at")
    list_filter = ("status", "source")
    search_fields = ("id", "source")

@admin.register(ExtractionRecord)
class ExtractionRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "email", "first_name", "last_name", "id_from_service")
    search_fields = ("email", "id_from_service")
