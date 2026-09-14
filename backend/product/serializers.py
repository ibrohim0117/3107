"""product app serializerlari."""

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Category, Product, Unit


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


class ProductCreateSerializer(serializers.ModelSerializer):
    """POST /api/v1/products/ — mahsulot yaratish (faqat admin).

    `views_count` va `created_by` tashqaridan berilmaydi.
    """

    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        error_messages={'does_not_exist': "Bunday faol kategoriya topilmadi."},
    )
    unit = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(),
        error_messages={'does_not_exist': "Bunday o'lchov birligi topilmadi."},
    )
    slug = serializers.SlugField(
        max_length=280,
        required=False,
        allow_blank=True,
        validators=[
            UniqueValidator(Product.objects.all(), message="Bu slug allaqachon band.")
        ],
        help_text="Bo'sh qoldirilsa nomdan avtomatik yasaladi.",
    )
    sku = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[
            UniqueValidator(Product.objects.all(), message="Bu SKU allaqachon mavjud.")
        ],
    )
    discount_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'slug',
            'category',
            'description',
            'price',
            'discount',
            'discount_price',
            'cost_price',
            'unit',
            'quantity',
            'min_quantity',
            'sku',
            'is_active',
            'views_count',
            'created_by',
            'created_at',
        )
        read_only_fields = ('id', 'discount_price', 'views_count', 'created_by', 'created_at')

    def validate_sku(self, value):
        # Bo'sh SKU NULL bo'lib saqlanadi — aks holda ikkinchi '' unique'ga uriladi
        return value or None
