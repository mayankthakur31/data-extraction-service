# Deployment

## Environment

Use `.env.example` as the template. Never commit `.env`.

## Docker

```bash
docker compose up --build
```

## Production

Recommended:

- PostgreSQL
- Redis
- Celery worker
- Gunicorn
- HTTPS reverse proxy
- API authentication enabled
- Strong Django secret key
- Real provider token stored as a secret
- DEBUG=False
