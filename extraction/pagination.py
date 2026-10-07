from rest_framework.pagination import LimitOffsetPagination
from django.conf import settings

class AssessmentPagination(LimitOffsetPagination):
    default_limit = settings.DEFAULT_PAGE_SIZE
    max_limit = settings.MAX_PAGE_SIZE
