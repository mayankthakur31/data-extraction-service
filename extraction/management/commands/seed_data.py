from django.core.management.base import BaseCommand
from extraction.models import ExtractionJob, ExtractionRecord

class Command(BaseCommand):
    help = "Seed deterministic assessment data."

    def handle(self, *args, **options):
        ExtractionRecord.objects.all().delete()
        ExtractionJob.objects.all().delete()

        pending = ExtractionJob.objects.create(
            source="seeded-demo",
            status=ExtractionJob.Status.PENDING,
            request_config={"filters": {}, "record_count": 0},
        )
        completed = ExtractionJob.objects.create(
            source="seeded-demo",
            status=ExtractionJob.Status.COMPLETED,
            record_count=3,
            request_config={"filters": {"demo": True}, "record_count": 3},
        )
        ExtractionJob.objects.create(
            source="seeded-demo",
            status=ExtractionJob.Status.CANCELLED,
            record_count=0,
            request_config={"filters": {}, "record_count": 0},
        )

        for i in range(3):
            ExtractionRecord.objects.create(
                job=completed,
                email=f"seed{i+1}@example.com",
                first_name=f"Seed{i+1}",
                last_name="User",
                id_from_service=f"seed-{i+1}",
                data={
                    "email": f"seed{i+1}@example.com",
                    "first_name": f"Seed{i+1}",
                    "last_name": "User",
                    "id_from_service": f"seed-{i+1}",
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded pending={pending.id}, completed={completed.id}, plus one cancelled job."
        ))
