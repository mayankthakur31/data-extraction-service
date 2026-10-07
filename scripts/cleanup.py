import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from extraction.models import ExtractionJob
deleted, _ = ExtractionJob.objects.all().delete()
print(f"Deleted {deleted} objects.")
