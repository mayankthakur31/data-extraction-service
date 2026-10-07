from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ExtractionJob",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("pending","Pending"),("in_progress","In Progress"),("completed","Completed"),("failed","Failed"),("cancelled","Cancelled")], db_index=True, default="pending", max_length=20)),
                ("source", models.CharField(db_index=True, default="external_service", max_length=255)),
                ("request_config", models.JSONField(blank=True, default=dict)),
                ("record_count", models.PositiveIntegerField(default=0)),
                ("error", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ExtractionRecord",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("first_name", models.CharField(blank=True, max_length=255, null=True)),
                ("last_name", models.CharField(blank=True, max_length=255, null=True)),
                ("id_from_service", models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ("data", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="records", to="extraction.extractionjob")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.AddIndex(model_name="extractionjob", index=models.Index(fields=["status","created_at"], name="job_status_created_idx")),
        migrations.AddIndex(model_name="extractionjob", index=models.Index(fields=["source","created_at"], name="job_source_created_idx")),
        migrations.AddIndex(model_name="extractionrecord", index=models.Index(fields=["job","id"], name="record_job_id_idx")),
    ]
