import pytest
from extraction.models import ExtractionJob, ExtractionRecord

@pytest.mark.django_db
def test_health(api_client):
    response = api_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.data["status"] == "ok"

@pytest.mark.django_db
def test_seeded_job_status(api_client):
    job = ExtractionJob.objects.create(source="test", status=ExtractionJob.Status.PENDING)
    response = api_client.get(f"/api/v1/scan/status/{job.id}")
    assert response.status_code == 200
    assert response.data["status"] == "pending"

@pytest.mark.django_db
def test_result_requires_completed(api_client):
    job = ExtractionJob.objects.create(source="test", status=ExtractionJob.Status.PENDING)
    response = api_client.get(f"/api/v1/scan/result/{job.id}")
    assert response.status_code == 409

@pytest.mark.django_db
def test_result_pagination(api_client):
    job = ExtractionJob.objects.create(source="test", status=ExtractionJob.Status.COMPLETED, record_count=5)
    for i in range(5):
        ExtractionRecord.objects.create(
            job=job, email=f"{i}@example.com", first_name="A",
            last_name="B", id_from_service=str(i), data={"n": i}
        )
    response = api_client.get(f"/api/v1/scan/result/{job.id}?limit=2&offset=2")
    assert response.status_code == 200
    assert len(response.data["results"]) == 2
    assert response.data["count"] == 5

@pytest.mark.django_db
def test_cancel_pending_job(api_client):
    job = ExtractionJob.objects.create(source="test", status=ExtractionJob.Status.PENDING)
    response = api_client.post(f"/api/v1/scan/cancel/{job.id}")
    assert response.status_code == 200
    job.refresh_from_db()
    assert job.status == ExtractionJob.Status.CANCELLED

@pytest.mark.django_db
def test_cancel_completed_job_is_conflict(api_client):
    job = ExtractionJob.objects.create(source="test", status=ExtractionJob.Status.COMPLETED)
    response = api_client.post(f"/api/v1/scan/cancel/{job.id}")
    assert response.status_code == 409

@pytest.mark.django_db
def test_remove_job(api_client):
    job = ExtractionJob.objects.create(source="test", status=ExtractionJob.Status.COMPLETED)
    ExtractionRecord.objects.create(job=job, email="x@example.com", data={})
    response = api_client.delete(f"/api/v1/scan/remove/{job.id}")
    assert response.status_code == 204
    assert not ExtractionJob.objects.filter(id=job.id).exists()

@pytest.mark.django_db
def test_nonexistent_job(api_client):
    import uuid
    response = api_client.get(f"/api/v1/scan/status/{uuid.uuid4()}")
    assert response.status_code == 404

@pytest.mark.django_db
def test_start_mock_extraction(api_client, settings):
    settings.EXTRACTION_PROVIDER = "mock"
    settings.CELERY_TASK_ALWAYS_EAGER = True
    response = api_client.post("/api/v1/scan/start", {
        "api_token": "demo-token",
        "source": "demo",
        "record_count": 3,
    }, format="json")
    assert response.status_code == 202
    job = ExtractionJob.objects.get(id=response.data["job_id"])
    assert job.status == ExtractionJob.Status.COMPLETED
    assert job.record_count == 3

@pytest.mark.django_db
def test_missing_token_for_generic_provider(api_client, settings):
    settings.EXTRACTION_PROVIDER = "generic"
    settings.EXTERNAL_API_TOKEN = ""
    response = api_client.post("/api/v1/scan/start", {
        "source": "demo",
        "record_count": 3,
    }, format="json")
    assert response.status_code == 401

@pytest.mark.django_db
def test_jobs_filter(api_client):
    ExtractionJob.objects.create(source="alpha", status=ExtractionJob.Status.COMPLETED)
    ExtractionJob.objects.create(source="beta", status=ExtractionJob.Status.PENDING)
    response = api_client.get("/api/v1/jobs/jobs?status=completed")
    assert response.status_code == 200
    assert all(item["status"] == "completed" for item in response.data["results"])

@pytest.mark.django_db
def test_statistics(api_client):
    ExtractionJob.objects.create(source="alpha", status=ExtractionJob.Status.COMPLETED, record_count=2)
    response = api_client.get("/api/v1/jobs/statistics")
    assert response.status_code == 200
    assert response.data["total_jobs"] == 1
    assert response.data["completed_jobs"] == 1

@pytest.mark.django_db
def test_malformed_start_request(api_client):
    response = api_client.post("/api/v1/scan/start", {"record_count": -1}, format="json")
    assert response.status_code == 400
