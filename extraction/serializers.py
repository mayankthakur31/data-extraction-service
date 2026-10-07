from rest_framework import serializers
from .models import ExtractionJob, ExtractionRecord

class StartExtractionSerializer(serializers.Serializer):
    api_token = serializers.CharField(required=False, allow_blank=True, write_only=True)
    source = serializers.CharField(required=True, max_length=255)
    record_count = serializers.IntegerField(required=False, min_value=0, max_value=10000, default=25)
    filters = serializers.DictField(required=False, default=dict)

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractionJob
        fields = [
            "id", "status", "source", "record_count", "error",
            "created_at", "started_at", "completed_at", "updated_at",
        ]

class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractionRecord
        fields = ["id", "email", "first_name", "last_name", "id_from_service", "data"]

class ErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
    message = serializers.CharField()
    details = serializers.JSONField(required=False)
