"""product app modellari testlari (TZ S2-10, S3-01, S3-04)."""

from decimal import Decimal

from django.contrib.admin.sites import site
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from users.models import User

from .models import Category, Comment, Like, Product, ProductImage, Unit


class CategoryTests(TestCase):
    def test_slug_avtomatik_yasaladi(self):
        category = Category.objects.create(name='Oziq-ovqat')
        self.assertEqual(category.slug, 'oziq-ovqat')

    def test_bir_xil_slugda_raqam_qoshiladi(self):
        birinchi = Category.objects.create(name='Sut')
        ikkinchi = Category.objects.create(name='sut')  # slugify natijasi bir xil

        self.assertEqual(birinchi.slug, 'sut')
        self.assertEqual(ikkinchi.slug, 'sut-2')

    def test_parent_bilan_ierarxiya(self):
        ota = Category.objects.create(name='Oziq-ovqat')
        bola = Category.objects.create(name='Sut mahsulotlari', parent=ota)
        self.assertEqual(list(ota.children.all()), [bola])
        self.assertEqual(str(bola), 'Oziq-ovqat → Sut mahsulotlari')

    def test_ozini_ota_qilib_bolmaydi(self):
        category = Category.objects.create(name='Oziq-ovqat')
        category.parent = category
        with self.assertRaises(ValidationError) as ctx:
            category.full_clean()
        self.assertIn('parent', ctx.exception.error_dict)

    def test_halqa_bloklanadi(self):
        ota = Category.objects.create(name='Oziq-ovqat')
        bola = Category.objects.create(name='Sut', parent=ota)
        ota.parent = bola
        with self.assertRaises(ValidationError):
            ota.full_clean()


class ProductTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Sut mahsulotlari')
        self.unit = Unit.objects.create(name='Kilogramm', short_name='kg')

    def create_product(self, **over):
        data = {
            'name': 'Qaymoq 20%',
            'category': self.category,
            'unit': self.unit,
            'price': Decimal('25000.00'),
            'quantity': Decimal('10.000'),
        }
        data.update(over)
        return Product.objects.create(**data)

    def test_slug_va_boshlangich_qiymatlar(self):
        product = self.create_product()
        self.assertEqual(product.slug, 'qaymoq-20')
        self.assertEqual(product.views_count, 0)
        self.assertTrue(product.is_active)
        self.assertTrue(product.in_stock)

    def test_chegirmasiz_discount_price_narxga_teng(self):
        product = self.create_product()
        self.assertEqual(product.discount, 0)
        self.assertFalse(product.has_discount)
        self.assertEqual(product.discount_price, Decimal('25000.00'))
        self.assertEqual(product.discount_amount, Decimal('0.00'))

    def test_discount_price_avtomatik_hisoblanadi(self):
        product = self.create_product(discount=Decimal('20.00'))
        self.assertTrue(product.has_discount)
        self.assertEqual(product.discount_amount, Decimal('5000.00'))
        self.assertEqual(product.discount_price, Decimal('20000.00'))

        # narx o'zgarsa chegirmali narx ham o'zgaradi — bazada saqlanmaydi
        product.price = Decimal('30000.00')
        self.assertEqual(product.discount_price, Decimal('24000.00'))

    def test_kasrli_chegirma_tiyingacha_yaxlitlanadi(self):
        product = self.create_product(price=Decimal('19999.00'), discount=Decimal('12.50'))
        self.assertEqual(product.discount_amount, Decimal('2499.88'))
        self.assertEqual(product.discount_price, Decimal('17499.12'))

    def test_chegirma_100_bolsa_narx_nol(self):
        product = self.create_product(discount=Decimal('100.00'))
        self.assertEqual(product.discount_price, Decimal('0.00'))

    def test_chegirma_0_100_oraligida(self):
        for notogri in (Decimal('-1.00'), Decimal('100.01'), Decimal('150.00')):
            with self.subTest(discount=notogri):
                product = self.create_product(name=f'Mahsulot {notogri}', discount=notogri)
                with self.assertRaises(ValidationError) as ctx:
                    product.full_clean()
                self.assertIn('discount', ctx.exception.error_dict)

    def test_discount_price_bazada_maydon_emas(self):
        self.assertNotIn(
            'discount_price', [f.name for f in Product._meta.get_fields()]
        )

    def test_register_view_sonni_oshiradi(self):
        product = self.create_product()
        product.register_view()
        product.register_view()
        product.refresh_from_db()
        self.assertEqual(product.views_count, 2)

    def test_views_count_formaga_tushmaydi(self):
        """Admin (va boshqa ModelForm) orqali ko'rishlar sonini o'zgartirib bo'lmaydi."""
        self.assertFalse(Product._meta.get_field('views_count').editable)

        model_admin = site._registry[Product]
        self.assertIn('views_count', model_admin.readonly_fields)

    def test_ishlatilayotgan_unit_ochirilmaydi(self):
        self.create_product()
        with self.assertRaises(ProtectedError):
            self.unit.delete()

    def test_ishlatilayotgan_kategoriya_ochirilmaydi(self):
        self.create_product()
        with self.assertRaises(ProtectedError):
            self.category.delete()

    def test_low_stock(self):
        product = self.create_product(quantity=Decimal('2.000'), min_quantity=Decimal('5.000'))
        self.assertTrue(product.is_low_stock)


class ProductImageTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Sut')
        unit = Unit.objects.create(name='Dona', short_name='dona')
        self.product = Product.objects.create(
            name='Qaymoq', category=category, unit=unit, price=Decimal('25000')
        )

    def test_birinchi_rasm_avtomatik_asosiy(self):
        rasm = ProductImage.objects.create(product=self.product, image='products/a.jpg')
        self.assertTrue(rasm.is_main)

    def test_faqat_bitta_asosiy_rasm(self):
        birinchi = ProductImage.objects.create(product=self.product, image='products/a.jpg')
        ikkinchi = ProductImage.objects.create(product=self.product, image='products/b.jpg')
        self.assertFalse(ikkinchi.is_main)

        ikkinchi.is_main = True
        ikkinchi.save()
        birinchi.refresh_from_db()

        self.assertFalse(birinchi.is_main)
        self.assertEqual(self.product.images.filter(is_main=True).count(), 1)


class LikeTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Sut')
        unit = Unit.objects.create(name='Dona', short_name='dona')
        self.product = Product.objects.create(
            name='Qaymoq', category=category, unit=unit, price=Decimal('25000')
        )
        self.user = User.objects.create_user(
            '901112233', 'Qwerty!2345', full_name='Ali', email='a@b.uz'
        )

    def test_bitta_user_bitta_marta_like_bosadi(self):
        Like.objects.create(user=self.user, product=self.product)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Like.objects.create(user=self.user, product=self.product)
        self.assertEqual(self.product.likes.count(), 1)

    def test_dublikat_like_formada_tushunarli_xato(self):
        Like.objects.create(user=self.user, product=self.product)
        takror = Like(user=self.user, product=self.product)
        with self.assertRaises(ValidationError) as ctx:
            takror.full_clean()
        self.assertIn('allaqachon like bosgan', str(ctx.exception))

    def test_boshqa_user_like_bosa_oladi(self):
        boshqa = User.objects.create_user(
            '901112234', 'Qwerty!2345', full_name='Vali', email='v@b.uz'
        )
        Like.objects.create(user=self.user, product=self.product)
        Like.objects.create(user=boshqa, product=self.product)
        self.assertEqual(self.product.likes.count(), 2)


class CommentTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Sut')
        unit = Unit.objects.create(name='Dona', short_name='dona')
        self.product = Product.objects.create(
            name='Qaymoq', category=category, unit=unit, price=Decimal('25000')
        )
        self.boshqa_product = Product.objects.create(
            name='Sut 1L', category=category, unit=unit, price=Decimal('12000')
        )
        self.user = User.objects.create_user(
            '901112233', 'Qwerty!2345', full_name='Ali', email='a@b.uz'
        )

    def test_izoh_va_javob(self):
        izoh = Comment.objects.create(user=self.user, product=self.product, text="Zo'r")
        javob = Comment.objects.create(
            user=self.user, product=self.product, text='Rahmat', parent=izoh
        )
        self.assertEqual(list(izoh.replies.all()), [javob])

    def test_javobga_javob_bloklanadi(self):
        izoh = Comment.objects.create(user=self.user, product=self.product, text="Zo'r")
        javob = Comment.objects.create(
            user=self.user, product=self.product, text='Rahmat', parent=izoh
        )
        uchinchi = Comment(
            user=self.user, product=self.product, text='Yana', parent=javob
        )
        with self.assertRaises(ValidationError) as ctx:
            uchinchi.full_clean()
        self.assertIn('parent', ctx.exception.error_dict)

    def test_javob_boshqa_mahsulotga_boglanmaydi(self):
        izoh = Comment.objects.create(user=self.user, product=self.product, text="Zo'r")
        javob = Comment(
            user=self.user, product=self.boshqa_product, text='Xato', parent=izoh
        )
        with self.assertRaises(ValidationError) as ctx:
            javob.full_clean()
        self.assertIn('parent', ctx.exception.error_dict)


class CategoryListAPITests(APITestCase):
    url = reverse('product:category-list')

    @classmethod
    def setUpTestData(cls):
        # 25 ta faol + 1 ta nofaol kategoriya
        for i in range(1, 26):
            Category.objects.create(name=f'Kategoriya {i:02d}')
        Category.objects.create(name='Yashirin', is_active=False)

    def test_ochiq_endpoint_va_standart_sahifa(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {'count', 'next', 'previous', 'results'})
        self.assertEqual(response.data['count'], 25)
        self.assertEqual(len(response.data['results']), 20)  # standart page_size
        self.assertIsNone(response.data['previous'])
        self.assertIn('page=2', response.data['next'])

    def test_ikkinchi_sahifa(self):
        response = self.client.get(self.url, {'page': 2})

        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNone(response.data['next'])
        self.assertIsNotNone(response.data['previous'])

    def test_page_size_parametri(self):
        response = self.client.get(self.url, {'page_size': 10})
        self.assertEqual(len(response.data['results']), 10)

    def test_page_size_100_dan_oshmaydi(self):
        for i in range(26, 131):
            Category.objects.create(name=f'Kategoriya {i:03d}')
        response = self.client.get(self.url, {'page_size': 1000})
        self.assertEqual(len(response.data['results']), 100)

    def test_mavjud_bolmagan_sahifa_404(self):
        response = self.client.get(self.url, {'page': 99})
        self.assertEqual(response.status_code, 404)

    def test_nofaol_kategoriya_korinmaydi(self):
        response = self.client.get(self.url, {'page_size': 100})
        names = [item['name'] for item in response.data['results']]
        self.assertNotIn('Yashirin', names)

    def test_element_maydonlari_va_parent(self):
        ota = Category.objects.get(name='Kategoriya 01')
        Category.objects.create(name='AAA ichki', parent=ota)

        item = self.client.get(self.url).data['results'][0]  # nom bo'yicha tartib
        self.assertEqual(set(item), {'id', 'name', 'slug', 'image', 'parent'})
        self.assertEqual(item['name'], 'AAA ichki')
        self.assertEqual(item['parent'], ota.pk)
