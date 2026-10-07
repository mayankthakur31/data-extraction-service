import re
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .auth import APIKeyAuthentication
from .models import ExtractionJob, ExtractionRecord
from .pagination import AssessmentPagination
from .serializers import StartExtractionSerializer, JobSerializer, RecordSerializer
from .services.extraction_service import JobService
from .services.external_api_service import ExternalServiceError
from .tasks import execute_extraction

job_service = JobService()
UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")

class BaseAPIView(APIView):
    authentication_classes = [APIKeyAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

class HealthView(BaseAPIView):
    @extend_schema(summary="Health check")
    def get(self, request):
        return Response({
            "status": "ok",
            "service": "data-extraction-service",
            "version": "1.0.0",
        })

class StartScanView(BaseAPIView):
    @extend_schema(
        summary="Start an extraction job",
        request=StartExtractionSerializer,
        responses={202: JobSerializer, 400: OpenApiResponse(description="Validation error"), 401: OpenApiResponse(description="Invalid token")},
    )
    def post(self, request):
        serializer = StartExtractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        token = data.get("api_token") or settings.EXTERNAL_API_TOKEN

        try:
            job = job_service.start_job(
                token=token,
                source=data["source"],
                record_count=data["record_count"],
                filters=data["filters"],
            )
        except ExternalServiceError as exc:
            return Response({"error": "Authentication failed", "message": exc.message}, status=exc.status_code or 401)
        except ValueError as exc:
            return Response({"error": "Conflict", "message": str(exc)}, status=409)

        execute_extraction.delay(str(job.id), token=token)
        return Response(
            {"job_id": str(job.id), "status": job.status, "message": "Extraction job accepted"},
            status=status.HTTP_202_ACCEPTED,
        )

class JobStatusView(BaseAPIView):
    @extend_schema(summary="Get extraction job status", responses={200: JobSerializer})
    def get(self, request, job_id):
        if not UUID_RE.match(str(job_id)):
            return Response({"error": "Not found", "message": "Job ID not found."}, status=404)
        job = get_object_or_404(ExtractionJob, id=job_id)
        return Response(JobSerializer(job).data)

class JobResultView(BaseAPIView):
    @extend_schema(
        summary="Get extracted records",
        parameters=[
            OpenApiParameter("limit", int, OpenApiParameter.QUERY, description="Number of records"),
            OpenApiParameter("offset", int, OpenApiParameter.QUERY, description="Starting offset"),
        ],
        responses={200: RecordSerializer(many=True)},
    )
    def get(self, request, job_id):
        if not UUID_RE.match(str(job_id)):
            return Response({"error": "Not found", "message": "Job ID not found."}, status=404)
        job = get_object_or_404(ExtractionJob, id=job_id)
        if job.status != ExtractionJob.Status.COMPLETED:
            return Response(
                {"error": "Job not completed", "message": "Extraction results are available only after the job is completed."},
                status=409,
            )
        queryset = ExtractionRecord.objects.filter(job=job).order_by("id")
        paginator = AssessmentPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(RecordSerializer(page, many=True).data)

class CancelJobView(BaseAPIView):
    @extend_schema(summary="Cancel a pending/in-progress job", responses={200: JobSerializer})
    def post(self, request, job_id):
        if not UUID_RE.match(str(job_id)):
            return Response({"error": "Not found", "message": "Job ID not found."}, status=404)
        try:
            job = job_service.cancel_job(job_id)
        except ExtractionJob.DoesNotExist:
            return Response({"error": "Not found", "message": "Job ID not found."}, status=404)
        except ValueError as exc:
            return Response({"error": "Conflict", "message": str(exc)}, status=409)
        return Response({"message": "Job cancelled successfully", "job": JobSerializer(job).data})

class RemoveJobView(BaseAPIView):
    @extend_schema(summary="Remove a job and its extracted data", responses={204: OpenApiResponse(description="Removed")})
    def delete(self, request, job_id):
        if not UUID_RE.match(str(job_id)):
            return Response({"error": "Not found", "message": "Job ID not found."}, status=404)
        try:
            job = ExtractionJob.objects.get(id=job_id)
        except ExtractionJob.DoesNotExist:
            return Response({"error": "Not found", "message": "Job ID not found."}, status=404)
        job.delete()
        return Response(status=204)

class JobsListView(BaseAPIView):
    @extend_schema(
        summary="List extraction jobs",
        parameters=[
            OpenApiParameter("limit", int, OpenApiParameter.QUERY),
            OpenApiParameter("offset", int, OpenApiParameter.QUERY),
            OpenApiParameter("status", str, OpenApiParameter.QUERY),
            OpenApiParameter("source", str, OpenApiParameter.QUERY),
        ],
        responses={200: JobSerializer(many=True)},
    )
    def get(self, request):
        queryset = ExtractionJob.objects.all()
        status_filter = request.query_params.get("status")
        source_filter = request.query_params.get("source")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if source_filter:
            queryset = queryset.filter(source=source_filter)
        paginator = AssessmentPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(JobSerializer(page, many=True).data)

class StatisticsView(BaseAPIView):
    @extend_schema(summary="Get job statistics")
    def get(self, request):
        return Response(job_service.statistics())
