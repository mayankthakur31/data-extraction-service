import pytest
from extraction.models import ExtractionJob
from extraction.services.extraction_service import JobService

@pytest.mark.django_db
def test_mock_job_service_executes(settings):
    settings.EXTRACTION_PROVIDER = "mock"
    service = JobService()
    job = service.start_job(
        token="demo",
        source="service",
        record_count=2,
        filters={},
    )
    service.execute_job(job.id, token="demo")
    job.refresh_from_db()
    assert job.status == ExtractionJob.Status.COMPLETED
    assert job.record_count == 2
