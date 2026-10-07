from celery import shared_task
from .services.extraction_service import JobService

@shared_task(bind=True, autoretry_for=(), max_retries=0)
def execute_extraction(self, job_id, token=None):
    return JobService().execute_job(job_id, token=token).id
