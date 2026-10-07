import logging
import time
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class ExternalServiceError(Exception):
    def __init__(self, message, status_code=None, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class ExternalAPIService:
    """Adapter around the third-party extraction provider."""

    def __init__(self):
        self.base_url = settings.EXTERNAL_API_BASE_URL
        self.timeout = settings.EXTERNAL_API_TIMEOUT
        self.verify_ssl = settings.EXTERNAL_API_VERIFY_SSL

    def extract(self, token: str, source: str, filters: dict, record_count: int) -> list[dict[str, Any]]:
        if settings.EXTRACTION_PROVIDER == "mock":
            return self._mock_extract(source, filters, record_count)

        if not token:
            raise ExternalServiceError("Invalid API token provided.", 401)

        if not self.base_url:
            raise ExternalServiceError("EXTERNAL_API_BASE_URL is not configured.", 503)

        payload = {
            "source": source,
            "filters": filters,
            "limit": record_count,
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        delay = 1
        for attempt in range(3):
            try:
                response = requests.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                )
                if response.status_code == 429:
                    if attempt == 2:
                        raise ExternalServiceError("External service rate limit exceeded.", 429)
                    time.sleep(delay)
                    delay *= 2
                    continue
                if response.status_code in (401, 403):
                    raise ExternalServiceError("Invalid or unauthorized API token.", response.status_code)
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict):
                    data = data.get("records", data.get("data", []))
                if not isinstance(data, list):
                    raise ExternalServiceError("External service returned an invalid data format.", 502)
                return [item for item in data if isinstance(item, dict)]
            except requests.Timeout as exc:
                if attempt == 2:
                    raise ExternalServiceError("External service request timed out.", 504) from exc
                time.sleep(delay)
                delay *= 2
            except requests.RequestException as exc:
                if attempt == 2:
                    raise ExternalServiceError("External service is temporarily unavailable.", 502) from exc
                time.sleep(delay)
                delay *= 2

        raise ExternalServiceError("External extraction failed.", 502)

    @staticmethod
    def _mock_extract(source, filters, record_count):
        records = []
        for i in range(record_count):
            records.append({
                "email": f"user{i+1}@example.com",
                "first_name": f"User{i+1}",
                "last_name": "Demo",
                "id_from_service": f"{source}-{i+1}",
                "source": source,
                "filters": filters,
            })
        return records
