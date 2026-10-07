import logging
from django.db import transaction
from django.utils import timezone
from django.db.models import Avg, Count, F, ExpressionWrapper, DurationField

from extraction.models import ExtractionJob, ExtractionRecord
from .external_api_service import ExternalAPIService, ExternalServiceError

logger = logging.getLogger(__name__)

class JobService:
    def __init__(self):
        self.external = ExternalAPIService()

    @transaction.atomic
    def start_job(self, *, token, source, record_count, filters):
        if not token and __import__("django.conf").conf.settings.EXTRACTION_PROVIDER != "mock":
            raise ExternalServiceError("Invalid API token provided.", 401)

        # Prevent duplicate active jobs for the same source/config.
        active = ExtractionJob.objects.filter(
            source=source,
            status__in=[ExtractionJob.Status.PENDING, ExtractionJob.Status.IN_PROGRESS],
            request_config={"filters": filters, "record_count": record_count},
        ).first()
        if active:
            raise ValueError(f"An active extraction job already exists: {active.id}")

        job = ExtractionJob.objects.create(
            source=source,
            request_config={"filters": filters, "record_count": record_count},
            status=ExtractionJob.Status.PENDING,
        )
        return job

    @transaction.atomic
    def execute_job(self, job_id, token=None):
        job = ExtractionJob.objects.select_for_update().get(id=job_id)
        if job.status == ExtractionJob.Status.CANCELLED:
            return job
        if job.status not in [ExtractionJob.Status.PENDING, ExtractionJob.Status.IN_PROGRESS]:
            return job

        job.status = ExtractionJob.Status.IN_PROGRESS
        job.started_at = timezone.now()
        job.error = None
        job.save(update_fields=["status", "started_at", "error", "updated_at"])

        try:
            config = job.request_config or {}
            records = self.external.extract(
                token=token,
                source=job.source,
                filters=config.get("filters", {}),
                record_count=config.get("record_count", 25),
            )
            if job.status == ExtractionJob.Status.CANCELLED:
                return job
            ExtractionRecord.objects.filter(job=job).delete()
            ExtractionRecord.objects.bulk_create([
                ExtractionRecord(
                    job=job,
                    email=item.get("email"),
                    first_name=item.get("first_name"),
                    last_name=item.get("last_name"),
                    id_from_service=str(item.get("id_from_service")) if item.get("id_from_service") is not None else None,
                    data=item,
                )
                for item in records
            ])
            job.record_count = len(records)
            job.status = ExtractionJob.Status.COMPLETED
            job.completed_at = timezone.now()
            job.save(update_fields=["record_count", "status", "completed_at", "updated_at"])
        except ExternalServiceError as exc:
            logger.exception("External extraction failed for %s", job_id)
            job.status = ExtractionJob.Status.FAILED
            job.error = exc.message
            job.completed_at = timezone.now()
            job.save(update_fields=["status", "error", "completed_at", "updated_at"])
        except Exception as exc:
            logger.exception("Unexpected extraction failure for %s", job_id)
            job.status = ExtractionJob.Status.FAILED
            job.error = "Unexpected extraction error."
            job.completed_at = timezone.now()
            job.save(update_fields=["status", "error", "completed_at", "updated_at"])
        return job

    @staticmethod
    def cancel_job(job_id):
        with transaction.atomic():
            job = ExtractionJob.objects.select_for_update().get(id=job_id)
            if job.status not in [ExtractionJob.Status.PENDING, ExtractionJob.Status.IN_PROGRESS]:
                raise ValueError(f"Job cannot be cancelled in current state: {job.status}")
            job.status = ExtractionJob.Status.CANCELLED
            job.completed_at = timezone.now()
            job.save(update_fields=["status", "completed_at", "updated_at"])
            return job

    @staticmethod
    def statistics():
        jobs = ExtractionJob.objects.all()
        completed = jobs.filter(status=ExtractionJob.Status.COMPLETED)
        avg = completed.exclude(started_at__isnull=True, completed_at__isnull=True).annotate(
            duration=ExpressionWrapper(F("completed_at") - F("started_at"), output_field=DurationField())
        ).aggregate(avg_duration=Avg("duration"))["avg_duration"]
        return {
            "total_jobs": jobs.count(),
            "completed_jobs": completed.count(),
            "pending_jobs": jobs.filter(status=ExtractionJob.Status.PENDING).count(),
            "in_progress_jobs": jobs.filter(status=ExtractionJob.Status.IN_PROGRESS).count(),
            "failed_jobs": jobs.filter(status=ExtractionJob.Status.FAILED).count(),
            "cancelled_jobs": jobs.filter(status=ExtractionJob.Status.CANCELLED).count(),
            "total_records": ExtractionRecord.objects.count(),
            "average_extraction_time_seconds": avg.total_seconds() if avg else 0,
        }
