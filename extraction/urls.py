from django.urls import path
from .views import (
    HealthView, StartScanView, JobStatusView, JobResultView,
    CancelJobView, RemoveJobView, JobsListView, StatisticsView,
)

urlpatterns = [
    path("health", HealthView.as_view(), name="health"),
    path("scan/start", StartScanView.as_view(), name="scan-start"),
    path("scan/status/<uuid:job_id>", JobStatusView.as_view(), name="scan-status"),
    path("scan/result/<uuid:job_id>", JobResultView.as_view(), name="scan-result"),
    path("scan/cancel/<uuid:job_id>", CancelJobView.as_view(), name="scan-cancel"),
    path("scan/remove/<uuid:job_id>", RemoveJobView.as_view(), name="scan-remove"),
    path("jobs/jobs", JobsListView.as_view(), name="jobs-list"),
    path("jobs/statistics", StatisticsView.as_view(), name="jobs-statistics"),
]
