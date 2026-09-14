"""
product app modellari.

TZ 3.4–3.10 asosida, bitta o'zgarish bilan: alohida `SubCategory` yo'q —
`Category` o'zini o'ziga `parent` orqali bog'laydi.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import F, Q
from django.utils.text import slugify

# Pul qiymatlarini yaxlitlash aniqligi
MONEY = Decimal('0.01')


class BaseModel(models.Model):
    """Umumiy sana maydonlari (TZ 3.1).

    TZ bo'yicha bu `common` app'da bo'lishi kerak; `common` yaratilgach
    o'sha yerga ko'chiriladi.
    """

    created_at = models.DateTimeField("Yaratilgan", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("Yangilangan", auto_now=True)

    class Meta:
        abstract = True


def unique_slugify(instance, value):
    """`value` dan takrorlanmas slug yasaydi: olma, olma-2, olma-3 ..."""
    base = slugify(value, allow_unicode=False) or 'obj'
    model = instance.__class__
    queryset = model.objects.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    slug, counter = base, 2
    while queryset.filter(slug=slug).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


class Category(BaseModel):
    """Kategoriya. `parent` orqali ichma-ich joylashadi (TZ 3.4 + 3.5 birlashtirilgan)."""

    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Ota kategoriya",
        help_text="Bo'sh bo'lsa — asosiy kategoriya.",
    )
    name = models.CharField("Nomi", max_length=150, unique=True)
    slug = models.SlugField(
        "Slug",
        max_length=170,
        unique=True,
        blank=True,
        help_text="Bo'sh qoldirilsa nomdan avtomatik yasaladi.",
    )
    image = models.ImageField("Rasm", upload_to='categories/', null=True, blank=True)
    is_active = models.BooleanField("Faol", default=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ['name']
        indexes = [models.Index(fields=['is_active', 'parent'])]

    def __str__(self):
        return f'{self.parent.name} → {self.name}' if self.parent_id else self.name

    def clean(self):
        # O'zini o'ziga yoki halqa (A→B→A) qilib bog'lab bo'lmaydi
        parent = self.parent
        while parent is not None:
            if parent.pk == self.pk and self.pk is not None:
                raise ValidationError(
                    {'parent': "Kategoriya o'zini (yoki o'z avlodini) ota qilib ololmaydi."}
                )
            parent = parent.parent

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def get_descendant_ids(self):
        """O'zi va barcha ichki kategoriyalarining id lari.

        Har bir daraja uchun bitta so'rov — chuqurlik kichik bo'lgani uchun yetarli.
        """
        ids = {self.pk}
        level = [self.pk]
        while level:
            level = list(
                Category.objects.filter(parent_id__in=level)
                .exclude(pk__in=ids)
                .values_list('pk', flat=True)
            )
            ids.update(level)
        return ids


class Unit(BaseModel):
    """O'lchov birligi: Kilogramm/kg, Dona/dona ... (TZ 3.6)."""

    name = models.CharField("Nomi", max_length=50, unique=True)
    short_name = models.CharField("Qisqartmasi", max_length=10, unique=True)

    class Meta:
        verbose_name = "O'lchov birligi"
        verbose_name_plural = "O'lchov birliklari"
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.short_name})'


class Product(BaseModel):
    """Mahsulot (TZ 3.7)."""

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name="Kategoriya",
    )
    name = models.CharField("Nomi", max_length=255)
    slug = models.SlugField(
        "Slug",
        max_length=280,
        unique=True,
        blank=True,
        help_text="Bo'sh qoldirilsa nomdan avtomatik yasaladi.",
    )
    description = models.TextField("Tavsif", blank=True)

    price = models.DecimalField(
        "Narx", max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    discount = models.DecimalField(
        "Chegirma (%)",
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="0 dan 100 gacha foizda. 0 bo'lsa chegirma yo'q.",
    )
    cost_price = models.DecimalField(
        "Tannarx",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Foyda hisoblash uchun. Mijozga ko'rsatilmaydi.",
    )

    unit = models.ForeignKey(
        Unit, on_delete=models.PROTECT, related_name='products', verbose_name="O'lchov birligi"
    )
    quantity = models.DecimalField(
        "Ombordagi qoldiq",
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
    )
    min_quantity = models.DecimalField(
        "Minimal qoldiq",
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Qoldiq shundan pastga tushsa 'yana kerak' ro'yxatiga tushadi.",
    )

    sku = models.CharField("SKU", max_length=50, unique=True, null=True, blank=True)
    views_count = models.PositiveIntegerField(
        "Ko'rishlar soni",
        default=0,
        editable=False,  # hech qanday formada (admin ham) tahrirlab bo'lmaydi
        help_text="Faqat mahsulot sahifasi ochilganda avtomatik oshadi.",
    )
    is_active = models.BooleanField("Faol", default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_products',
        verbose_name="Kim qo'shgan",
    )

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'category']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def register_view(self):
        """Ko'rishlar sonini +1 qiladi (TZ S2-06).

        `F()` ishlatiladi — bir vaqtda kelgan so'rovlarda hisob buzilmaydi.
        `views_count` ni qo'lda o'zgartirishning yagona ruxsat etilgan yo'li shu.
        """
        type(self).objects.filter(pk=self.pk).update(views_count=F('views_count') + 1)

    @property
    def has_discount(self):
        return bool(self.discount)

    @property
    def discount_amount(self):
        """Chegirma summasi: narxning `discount` foizi."""
        return (self.price * self.discount / 100).quantize(MONEY, rounding=ROUND_HALF_UP)

    @property
    def discount_price(self):
        """Mijoz to'laydigan narx — `price` dan `discount` foiz ayirilgani.

        Bazada saqlanmaydi, har safar `price` va `discount` dan hisoblanadi.
        Chegirma 0 bo'lsa asosiy narxning o'zi qaytadi.
        """
        return (self.price - self.discount_amount).quantize(MONEY, rounding=ROUND_HALF_UP)

    @property
    def in_stock(self):
        return self.quantity > 0

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_quantity


class ProductImage(BaseModel):
    """Mahsulot rasmi. Bitta mahsulotda faqat bitta `is_main=True` (TZ 3.8)."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='images', verbose_name="Mahsulot"
    )
    image = models.ImageField("Rasm", upload_to='products/')
    is_main = models.BooleanField("Asosiy rasm", default=False)

    class Meta:
        verbose_name = "Mahsulot rasmi"
        verbose_name_plural = "Mahsulot rasmlari"
        ordering = ['-is_main', 'created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['product'],
                condition=Q(is_main=True),
                name='uniq_main_image_per_product',
            )
        ]

    def __str__(self):
        return f'{self.product.name} rasmi'

    def save(self, *args, **kwargs):
        siblings = ProductImage.objects.filter(product_id=self.product_id).exclude(pk=self.pk)
        # Birinchi rasm avtomatik asosiy bo'ladi
        if not self.is_main and not siblings.exists():
            self.is_main = True

        with transaction.atomic():
            if self.is_main:
                siblings.filter(is_main=True).update(is_main=False)
            super().save(*args, **kwargs)


class Like(BaseModel):
    """Mahsulotga like. Bitta user bitta mahsulotga faqat bir marta (TZ 3.9)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name="Foydalanuvchi",
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='likes', verbose_name="Mahsulot"
    )

    class Meta:
        verbose_name = "Like"
        verbose_name_plural = "Like'lar"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                name='uniq_like_user_product',
                violation_error_message="Bu foydalanuvchi mahsulotga allaqachon like bosgan.",
            )
        ]
        indexes = [models.Index(fields=['product'])]

    def __str__(self):
        return f'{self.user} ♥ {self.product}'


class Comment(BaseModel):
    """Izoh va unga javob (TZ 3.10)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Foydalanuvchi",
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='comments', verbose_name="Mahsulot"
    )
    text = models.TextField("Matn")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name="Javob berilayotgan izoh",
    )
    is_active = models.BooleanField("Faol", default=True)

    class Meta:
        verbose_name = "Izoh"
        verbose_name_plural = "Izohlar"
        ordering = ['-created_at']
        indexes = [models.Index(fields=['product', 'is_active'])]

    def __str__(self):
        return f'{self.user}: {self.text[:40]}'

    def clean(self):
        if self.parent_id is None:
            return
        if self.parent_id == self.pk:
            raise ValidationError({'parent': "Izoh o'ziga javob bo'la olmaydi."})
        if self.parent.product_id != self.product_id:
            raise ValidationError({'parent': "Javob boshqa mahsulot izohiga bog'lanmaydi."})
        # TZ S3-04: 1 daraja chuqurlik yetarli
        if self.parent.parent_id is not None:
            raise ValidationError({'parent': "Javobga javob yozib bo'lmaydi."})
