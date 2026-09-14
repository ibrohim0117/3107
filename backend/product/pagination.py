"""product app pagination klasslari (TZ 6.3)."""

from rest_framework.pagination import PageNumberPagination


class CatalogPagination(PageNumberPagination):
    """`?page=2&page_size=10` ko'rinishidagi sahifalash.

    - standart: 20 ta element
    - `page_size` ni mijoz o'zi berishi mumkin, lekin 100 dan oshmaydi
    """

    page_size = 20
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 100
