# Data Extraction Service

A Django + Django REST Framework backend implementing the Data Extraction Service assessment.

## What is included

- Layered Django architecture: API -> services -> data layer
- Extraction job lifecycle: `pending -> in_progress -> completed/failed/cancelled`
- Seeded/mock extraction workflow for deterministic testing
- Generic external API provider for real extraction
- Pagination and filtering
- Job statistics
- Health check
- Cancellation and removal
- Validation and consistent error responses
- Optional API-key authentication
- DRF throttling
- OpenAPI + Swagger UI
- Unit/integration tests
- Docker + PostgreSQL + Redis
- CI workflow
- `.env.example`
- Seed script and test fixtures

The assessment documentation defines the required endpoints and focuses on seeded data tests, real extraction tests, and edge-case behavior. fileciteturn0file0L31-L38

## API endpoints

| Method | Endpoint |
|---|---|
| POST | `/api/v1/scan/start` |
| GET | `/api/v1/scan/status/<job_id>` |
| GET | `/api/v1/scan/result/<job_id>` |
| POST | `/api/v1/scan/cancel/<job_id>` |
| DELETE | `/api/v1/scan/remove/<job_id>` |
| GET | `/api/v1/jobs/jobs` |
| GET | `/api/v1/jobs/statistics` |
| GET | `/api/v1/health` |
| GET | `/api/docs/` |
| GET | `/api/schema/` |

The endpoint set follows the assessment document. fileciteturn0file0L148-L160

## Quick start - Windows

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-test.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Open:

- Swagger UI: http://127.0.0.1:8000/api/docs/
- Schema: http://127.0.0.1:8000/api/schema/
- Health: http://127.0.0.1:8000/api/v1/health

## Quick start - Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

## Seeded demo data

The seed command creates:

- one pending job
- one completed job with sample records
- one cancelled job

Run:

```bash
python manage.py seed_data
```

Then use Swagger to test status, results, jobs, statistics, cancellation and removal.

## Start a mock extraction

With the default `EXTRACTION_PROVIDER=mock`:

```http
POST /api/v1/scan/start
Content-Type: application/json

{
  "api_token": "demo-token",
  "source": "demo",
  "record_count": 25
}
```

Expected response:

```json
{
  "job_id": "uuid",
  "status": "pending",
  "message": "Extraction job accepted"
}
```

Because `.env.example` sets `CELERY_TASK_ALWAYS_EAGER=True`, the local task executes immediately. Set it to `False` and run a Celery worker for a real asynchronous setup.

## Real extraction provider

Set:

```env
EXTRACTION_PROVIDER=generic
EXTERNAL_API_BASE_URL=https://your-provider.example/api/extract
EXTERNAL_API_TOKEN=
```

You may also send the provider token in the request body:

```json
{
  "api_token": "provider-token",
  "source": "contacts",
  "record_count": 100
}
```

The generic provider sends a POST request with a bearer token and expects a JSON response containing either:

```json
{
  "records": [
    {
      "email": "a@example.com",
      "first_name": "A",
      "last_name": "User",
      "id_from_service": "123"
    }
  ]
}
```

or a JSON array of records.

No provider-specific API contract was supplied in the assessment document, so this adapter is intentionally generic rather than pretending to implement an undocumented vendor API. The assessment only requires a valid token and real third-party extraction workflow. fileciteturn0file0L92-L117

## Pagination

Results:

```text
GET /api/v1/scan/result/<job_id>?limit=20&offset=0
```

Jobs:

```text
GET /api/v1/jobs/jobs?limit=20&offset=0&status=completed
```

The assessment specifically calls for pagination and limit/offset validation. fileciteturn0file0L134-L140

## Error behavior

The service handles the assessment edge cases including:

- missing/invalid API token
- non-existent job ID
- results requested before completion
- cancellation of completed/failed jobs
- malformed JSON/missing required fields
- duplicate active extraction requests
- external provider failures
- invalid pagination
- job ID validation
- external rate-limit responses

These correspond to the documented edge-case requirements. fileciteturn0file0L165-L203

## Testing

```bash
pytest -q
```

The test suite covers health, seeded jobs, pagination, statistics, cancellation, removal, incomplete results, missing tokens, duplicate jobs and malformed input.

The testing strategy follows the provided guidance's unit/integration/E2E structure and its emphasis on assertions beyond status codes. fileciteturn0file1L534-L598

## Docker

```bash
docker compose up --build
```

The compose setup starts:

- Django/Gunicorn
- PostgreSQL
- Redis
- Celery worker

For Docker, create `.env` first and set:

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/data_extraction
CELERY_TASK_ALWAYS_EAGER=False
```

## Architecture

```text
config/
  settings.py
  urls.py
  celery.py

extraction/
  models.py
  serializers.py
  views.py
  urls.py
  services/
    extraction_service.py
    external_api_service.py
  management/commands/seed_data.py

tests/
  test_api.py
  test_services.py
```

This keeps API handling, business logic and data persistence separated, matching the layered architecture requirement. fileciteturn0file1L22-L40

## Security notes

- Secrets are environment variables.
- `.env` is ignored by Git.
- Optional `X-API-Key` authentication is supported.
- DRF throttling is enabled.
- Inputs are validated with serializers.
- External requests have timeouts and retries.
- Provider tokens are not stored in the database.

The service guidelines emphasize configuration management, validation, authentication, rate limiting and security-first design. fileciteturn0file1L371-L430 fileciteturn0file1L1022-L1110

## Submission checklist

Before submitting:

1. Run `pytest -q`.
2. Run the server and open Swagger.
3. Run `python manage.py seed_data`.
4. Test the required endpoints.
5. Confirm `.env` is NOT committed.
6. Commit and push the complete project to GitHub.
7. Email the repository using the assessment's requested subject.
8. Send the repository privately in the specified Teams channel.

