from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100

    def __init__(self):
        super().__init__()
        self.page_size = settings.REST_FRAMEWORK.get("PAGE_SIZE", 20)
