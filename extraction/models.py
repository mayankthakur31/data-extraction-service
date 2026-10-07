import uuid
from django.db import models

class ExtractionJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    source = models.CharField(max_length=255, default="external_service", db_index=True)
    request_config = models.JSONField(default=dict, blank=True)
    record_count = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="job_status_created_idx"),
            models.Index(fields=["source", "created_at"], name="job_source_created_idx"),
        ]

    def __str__(self):
        return f"{self.id} ({self.status})"

class ExtractionRecord(models.Model):
    id = models.BigAutoField(primary_key=True)
    job = models.ForeignKey(
        ExtractionJob,
        on_delete=models.CASCADE,
        related_name="records",
    )
    email = models.EmailField(blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    id_from_service = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["job", "id"], name="record_job_id_idx"),
        ]
