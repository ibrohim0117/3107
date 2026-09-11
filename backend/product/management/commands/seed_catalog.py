"""
Katalogni sinov ma'lumotlari bilan to'ldiradi (TZ S2-03).

    python manage.py seed_catalog

Qayta-qayta ishga tushirish xavfsiz — mavjud yozuvlar takrorlanmaydi
(`get_or_create` ishlatiladi).
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from product.models import Category, Comment, Like, Product, Unit
from users.models import User

UNITS = [
    ('Kilogramm', 'kg'),
    ('Litr', 'l'),
    ('Dona', 'dona'),
    ('Metr', 'm'),
    ('Quti', 'quti'),
]

# (nom, ota kategoriya nomi yoki None)
CATEGORIES = [
    ('Oziq-ovqat', None),
    ('Sut mahsulotlari', 'Oziq-ovqat'),
    ('Ichimliklar', 'Oziq-ovqat'),
    ('Maishiy texnika', None),
    ('Telefonlar', 'Maishiy texnika'),
]

# (nom, kategoriya, birlik, narx, chegirma %, qoldiq, min qoldiq, sku)
PRODUCTS = [
    ("Qaymoq 20%", 'Sut mahsulotlari', 'Dona', '25000.00', '0', '40.000', '10.000', 'SUT-001'),
    ('Sut 1L', 'Sut mahsulotlari', 'Litr', '12000.00', '10.00', '120.000', '30.000', 'SUT-002'),
    ('Tabiiy olma sharbati 1L', 'Ichimliklar', 'Litr', '18000.00', '12.50', '60.000', '20.000', 'ICH-001'),
    ('Samsung Galaxy A55', 'Telefonlar', 'Dona', '4500000.00', '5.00', '7.000', '3.000', 'TEL-001'),
    ('Guruch Lazer 1kg', 'Oziq-ovqat', 'Kilogramm', '22000.00', '0', '3.000', '15.000', 'OZQ-001'),
]

# (mahsulot nomi, izoh matni, javobmi)
COMMENTS = [
    ('Sut 1L', "Sifati zo'r, yetkazib berish tez bo'ldi.", False),
    ('Sut 1L', "Rahmat, fikringiz uchun!", True),  # yuqoridagi izohga javob
    ("Qaymoq 20%", 'Narxi biroz qimmat, lekin mazasi yaxshi.', False),
    ('Samsung Galaxy A55', 'Kamerasi kutganimdan ham yaxshi chiqdi.', False),
    ('Guruch Lazer 1kg', 'Omborda qolmabdi, qachon keladi?', False),
]

LIKES = [
    ('Sut 1L', 0),
    ("Qaymoq 20%", 0),
    ('Samsung Galaxy A55', 0),
    ('Sut 1L', 1),
    ('Tabiiy olma sharbati 1L', 1),
]


class Command(BaseCommand):
    help = "Katalogga sinov ma'lumotlarini qo'shadi: 5 ta unit, kategoriya, mahsulot, like va izoh."

    @transaction.atomic
    def handle(self, *args, **options):
        users = list(User.objects.order_by('id')[:2])
        if not users:
            self.stderr.write(
                self.style.ERROR(
                    "Bazada foydalanuvchi yo'q. Avval `createsuperuser` yoki "
                    "`/api/v1/auth/register/` orqali user yarating."
                )
            )
            return
        if len(users) == 1:
            users = users * 2
        author = User.objects.filter(is_staff=True).order_by('id').first()

        units = {}
        for name, short_name in UNITS:
            unit, created = Unit.objects.get_or_create(
                name=name, defaults={'short_name': short_name}
            )
            units[name] = unit
            self.log('Unit', unit, created)

        categories = {}
        for name, parent_name in CATEGORIES:
            category, created = Category.objects.get_or_create(
                name=name, defaults={'parent': categories.get(parent_name)}
            )
            categories[name] = category
            self.log('Kategoriya', category, created)

        products = {}
        for name, cat, unit, price, discount, qty, min_qty, sku in PRODUCTS:
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'category': categories[cat],
                    'unit': units[unit],
                    'price': Decimal(price),
                    'discount': Decimal(discount),
                    'cost_price': (Decimal(price) * Decimal('0.7')).quantize(Decimal('0.01')),
                    'quantity': Decimal(qty),
                    'min_quantity': Decimal(min_qty),
                    'sku': sku,
                    'created_by': author,
                },
            )
            products[name] = product
            self.log('Mahsulot', product, created)

        for product_name, index in LIKES:
            like, created = Like.objects.get_or_create(
                user=users[index], product=products[product_name]
            )
            self.log('Like', like, created)

        oxirgi_izoh = None
        for product_name, text, is_reply in COMMENTS:
            comment, created = Comment.objects.get_or_create(
                user=users[1 if is_reply else 0],
                product=products[product_name],
                text=text,
                defaults={'parent': oxirgi_izoh if is_reply else None},
            )
            if not is_reply:
                oxirgi_izoh = comment
            self.log('Izoh', comment, created)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Bazadagi jami:'))
        for label, model in (
            ("O'lchov birligi", Unit),
            ('Kategoriya', Category),
            ('Mahsulot', Product),
            ('Like', Like),
            ('Izoh', Comment),
        ):
            self.stdout.write(f'  {label:18} {model.objects.count()}')

    def log(self, label, obj, created):
        belgi = self.style.SUCCESS('+ qo\'shildi') if created else self.style.WARNING('~ mavjud')
        self.stdout.write(f'{belgi}  {label}: {obj}')
