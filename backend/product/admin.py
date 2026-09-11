"""product app uchun Django admin sozlamalari (TZ S2-01, S2-02, S5-12)."""

from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import Category, Comment, Like, Product, ProductImage, Unit


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'products_count', 'children_count', 'is_active', 'created_at')
    list_display_links = ('name',)
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('parent',)
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 30

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('parent')
            .annotate(_products=Count('products', distinct=True), _children=Count('children', distinct=True))
        )

    @admin.display(description="Mahsulotlar", ordering='_products')
    def products_count(self, obj):
        return obj._products

    @admin.display(description="Ichki kategoriya", ordering='_children')
    def children_count(self, obj):
        return obj._children


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name')
    search_fields = ('name', 'short_name')
    readonly_fields = ('created_at', 'updated_at')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'preview', 'is_main')
    readonly_fields = ('preview',)

    @admin.display(description="Ko'rinishi")
    def preview(self, obj):
        if not obj.image:
            return "—"
        return format_html('<img src="{}" style="max-height:80px;border-radius:6px;" />', obj.image.url)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'price',
        'discount',
        'discount_price_display',
        'quantity',
        'unit',
        'views_count',
        'likes_count',
        'is_active',
    )
    list_display_links = ('name',)
    list_filter = ('is_active', 'category', 'unit', 'created_at')
    search_fields = ('name', 'slug', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('category', 'unit')
    inlines = [ProductImageInline]
    list_per_page = 25
    date_hierarchy = 'created_at'

    # views_count `editable=False` — formaga umuman tushmaydi, bu yerda faqat ko'rsatiladi
    readonly_fields = (
        'discount_price_display',
        'views_count',
        'likes_count',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (None, {'fields': ('name', 'slug', 'category', 'description', 'is_active')}),
        ("Narxlar", {
            'fields': ('price', 'discount', 'discount_price_display', 'cost_price'),
            'description': "Chegirmali narx `price` va `discount` dan avtomatik hisoblanadi.",
        }),
        ("Ombor", {'fields': ('unit', 'quantity', 'min_quantity', 'sku')}),
        ("Statistika", {
            'fields': ('views_count', 'likes_count'),
            'description': "Faqat o'qish uchun — ko'rishlar soni sayt orqali avtomatik oshadi.",
        }),
        ("Xizmat", {'fields': ('created_by', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('category', 'unit')
            .annotate(_likes=Count('likes', distinct=True))
        )

    @admin.display(description="Chegirmali narx")
    def discount_price_display(self, obj):
        if obj.pk is None or obj.price is None:
            return "—"
        if not obj.has_discount:
            return obj.price
        return format_html(
            '<s style="opacity:.6">{}</s> <b>{}</b>', obj.price, obj.discount_price
        )

    @admin.display(description="Like", ordering='_likes')
    def likes_count(self, obj):
        return getattr(obj, '_likes', obj.likes.count())

    def save_model(self, request, obj, form, change):
        if not change and obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'preview', 'is_main', 'created_at')
    list_filter = ('is_main',)
    search_fields = ('product__name',)
    autocomplete_fields = ('product',)
    readonly_fields = ('preview', 'created_at', 'updated_at')
    list_select_related = ('product',)

    @admin.display(description="Ko'rinishi")
    def preview(self, obj):
        if not obj.image:
            return "—"
        return format_html('<img src="{}" style="max-height:60px;border-radius:6px;" />', obj.image.url)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__phone_number', 'user__full_name', 'product__name')
    autocomplete_fields = ('user', 'product')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user', 'product')
    list_per_page = 50


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'short_text', 'parent', 'is_active', 'created_at')
    list_display_links = ('short_text',)
    list_filter = ('is_active', 'created_at')
    search_fields = ('text', 'user__phone_number', 'user__full_name', 'product__name')
    autocomplete_fields = ('user', 'product', 'parent')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user', 'product', 'parent')
    list_per_page = 50

    @admin.display(description="Matn")
    def short_text(self, obj):
        return obj.text[:60] + ('…' if len(obj.text) > 60 else '')
