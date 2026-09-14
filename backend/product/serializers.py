"""product app serializerlari."""

from rest_framework import serializers

from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    """GET /api/v1/categories/ — kategoriya ro'yxati elementi."""

    # view'da select_related('parent') — har kategoriya uchun alohida so'rov ketmaydi
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'image', 'parent', 'parent_name')
        read_only_fields = fields


class ProductListSerializer(serializers.ModelSerializer):
    """GET /api/v1/products/ — ro'yxat uchun yengil ko'rinish (TZ S2-04).

    `description`, `cost_price` kabi og'ir/ichki maydonlar bu yerda yo'q.
    """

    # view'da select_related('category', 'unit') — har mahsulot uchun alohida so'rov ketmaydi
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit = serializers.CharField(source='unit.short_name', read_only=True)
    discount_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'slug',
            'category',
            'category_name',
            'price',
            'discount',
            'discount_price',
            'unit',
            'in_stock',
            'main_image',
        )
        read_only_fields = fields

    def get_main_image(self, obj) -> str | None:
        # view'dagi Prefetch(to_attr='main_images') — qo'shimcha so'rov yo'q
        images = getattr(obj, 'main_images', None)
        if not images:
            return None
        request = self.context.get('request')
        url = images[0].image.url
        return request.build_absolute_uri(url) if request else url
