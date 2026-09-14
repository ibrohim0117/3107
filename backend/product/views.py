"""product app view'lari."""

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Category
from .pagination import CatalogPagination
from .serializers import CategorySerializer


@extend_schema(
    tags=['catalog'],
    summary="Kategoriyalar ro'yxati",
    description=(
        "Faol kategoriyalar ro'yxati, sahifalangan holda.\n\n"
        "- `page` — sahifa raqami (1 dan boshlanadi)\n"
        "- `page_size` — bir sahifadagi elementlar soni (standart 20, maksimal 100)\n\n"
        "`parent` bo'sh bo'lsa — asosiy kategoriya, aks holda ota kategoriyaning `id` si."
    ),
)
class CategoryListView(generics.ListAPIView):
    """GET /api/v1/categories/ — ochiq."""

    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = CatalogPagination
    queryset = Category.objects.filter(is_active=True).order_by('name')
