"""product app view'lari."""

from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny

from .filters import ProductFilter
from .models import Category, Product, ProductImage
from .pagination import CatalogPagination
from .serializers import CategorySerializer, ProductListSerializer


@extend_schema(
    tags=['catalog'],
    summary="Kategoriyalar ro'yxati",
    description=(
        "Faol kategoriyalar ro'yxati, sahifalangan holda.\n\n"
        "- `page` — sahifa raqami (1 dan boshlanadi)\n"
        "- `page_size` — bir sahifadagi elementlar soni (standart 20, maksimal 100)\n\n"
        "`parent` va `parent_name` bo'sh (`null`) bo'lsa — asosiy kategoriya, "
        "aks holda ota kategoriyaning `id` si va nomi."
    ),
)
class CategoryListView(generics.ListAPIView):
    """GET /api/v1/categories/ — ochiq."""

    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = CatalogPagination
    queryset = Category.objects.filter(is_active=True).select_related('parent').order_by('name')


@extend_schema(
    tags=['catalog'],
    summary="Mahsulotlar ro'yxati",
    description=(
        "Faol mahsulotlar ro'yxati. Login talab qilinmaydi.\n\n"
        "**Sahifalash:** `page`, `page_size` (standart 20, maksimal 100)\n\n"
        "**Filter:**\n"
        "- `category` — kategoriya id si; ichki kategoriyalardagi mahsulotlar ham chiqadi\n"
        "- `min_price`, `max_price` — asosiy narx (`price`) bo'yicha oraliq, chegaralar kiradi\n\n"
        "**Qidiruv:** `search` — mahsulot nomi va tavsifi (`description`) ichidan, "
        "katta-kichik harf farqsiz.\n\n"
        "Parametrlarni birga ishlatish mumkin: "
        "`?category=1&min_price=10000&max_price=30000&search=sut&page=1`"
    ),
)
class ProductListView(generics.ListAPIView):
    """GET /api/v1/products/ — ochiq."""

    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    pagination_class = CatalogPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True, category__is_active=True)
            .select_related('category', 'unit')
            .prefetch_related(
                Prefetch(
                    'images',
                    queryset=ProductImage.objects.filter(is_main=True),
                    to_attr='main_images',
                )
            )
            .order_by('-created_at', '-id')
        )
