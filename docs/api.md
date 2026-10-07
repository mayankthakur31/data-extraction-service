# API Reference

## Health

`GET /api/v1/health`

Response:

```json
{"status":"ok","service":"data-extraction-service","version":"1.0.0"}
```

## Start extraction

`POST /api/v1/scan/start`

```json
{
  "api_token": "demo-token",
  "source": "contacts",
  "record_count": 25,
  "filters": {}
}
```

Returns `202 Accepted`.

## Status

`GET /api/v1/scan/status/{job_id}`

## Results

`GET /api/v1/scan/result/{job_id}?limit=20&offset=0`

Returns `409` until the job is completed.

## Cancel

`POST /api/v1/scan/cancel/{job_id}`

Only pending/in-progress jobs can be cancelled.

## Remove

`DELETE /api/v1/scan/remove/{job_id}`

Deletes the job and cascades its extracted records.

## Jobs

`GET /api/v1/jobs/jobs?status=completed&source=contacts&limit=20&offset=0`

## Statistics

`GET /api/v1/jobs/statistics`

## Swagger

`GET /api/docs/`
