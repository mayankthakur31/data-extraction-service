# Troubleshooting

## `No module named django`

Activate the virtual environment and run:

```bash
pip install -r requirements.txt
```

## Swagger is blank

Run migrations and restart the server:

```bash
python manage.py migrate
python manage.py runserver
```

## Real provider returns 503

Check:

- `EXTRACTION_PROVIDER=generic`
- `EXTERNAL_API_BASE_URL`
- provider availability
- provider token
- network/SSL settings

## Celery jobs do not run

For real asynchronous mode:

```env
CELERY_TASK_ALWAYS_EAGER=False
```

Start Redis and a worker:

```bash
celery -A config worker -l info
```

On Windows, if needed:

```bash
celery -A config worker -l info --pool=solo
```
