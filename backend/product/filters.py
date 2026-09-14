"""product app filterlari (django-filter)."""

import django_filters

from .models import Category, Product


class ProductFilter(django_filters.FilterSet):
    """`?category=1&min_price=10000&max_price=50000`"""

    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True),
        method='filter_category',
        label="Kategoriya id si (ichki kategoriyalardagi mahsulotlar ham chiqadi)",
    )
    min_price = django_filters.NumberFilter(
        field_name='price', lookup_expr='gte', min_value=0, label="Minimal narx"
    )
    max_price = django_filters.NumberFilter(
        field_name='price', lookup_expr='lte', min_value=0, label="Maksimal narx"
    )

    class Meta:
        model = Product
        fields = ('category', 'min_price', 'max_price')

    def filter_category(self, queryset, name, value):
        # "Oziq-ovqat" tanlansa "Sut mahsulotlari" dagi mahsulotlar ham chiqadi
        return queryset.filter(category_id__in=value.get_descendant_ids())
