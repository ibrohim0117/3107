"""users app testlari (TZ S1-02 DoD: normalizatsiya testlari)."""

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse_lazy
from rest_framework.test import APITestCase

from .models import User, UserRole, VerificationCode
from .utils import normalize_phone

VALID = '+998901112233'


class NormalizePhoneTests(TestCase):
    def test_har_xil_format_bir_xil_natija(self):
        for raw in [
            '901112233',
            '90 111 22 33',
            '998901112233',
            '+998901112233',
            '+998 90 111 22 33',
            '+998 (90) 111-22-33',
            '00998901112233',
        ]:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_phone(raw), VALID)

    def test_notogri_raqam_xato_beradi(self):
        for raw in ['12345', '9011122334455', 'salom', '+7 900 111 22 33']:
            with self.subTest(raw=raw):
                with self.assertRaises(ValidationError):
                    normalize_phone(raw)

    def test_bosh_qiymat_ozgarmaydi(self):
        self.assertEqual(normalize_phone(''), '')
        self.assertIsNone(normalize_phone(None))


class UserModelTests(TestCase):
    def test_create_user_raqamni_normalizatsiya_qiladi(self):
        user = User.objects.create_user('901112233', 'Parol123!', full_name='Ali', email='a@b.uz')
        self.assertEqual(user.phone_number, VALID)
        self.assertFalse(user.is_active)  # kod tasdiqlanmaguncha
        self.assertIsNone(user.username)

    def test_full_clean_ham_normalizatsiya_qiladi(self):
        user = User(phone_number='90 111 22 33', full_name='Ali', email='a@b.uz')
        user.full_clean(exclude=['password'])
        self.assertEqual(user.phone_number, VALID)

    def test_notogri_raqam_full_clean_da_rad_etiladi(self):
        user = User(phone_number='123', full_name='Ali', email='a@b.uz')
        with self.assertRaises(ValidationError) as ctx:
            user.full_clean(exclude=['password'])
        self.assertIn('phone_number', ctx.exception.error_dict)

    def test_dublikat_raqam_turli_formatda_ham_topiladi(self):
        User.objects.create_user('901112233', 'Parol123!', full_name='Ali', email='a@b.uz')
        user = User(phone_number='+998 90 111 22 33', full_name='Vali', email='v@b.uz')
        with self.assertRaises(ValidationError):
            user.full_clean(exclude=['password'])

    def test_admin_roli_is_staff_ni_yoqadi(self):
        user = User.objects.create_user('901112233', 'Parol123!', full_name='Ali', email='a@b.uz')
        user.role = UserRole.ADMIN
        user.save()
        user.refresh_from_db()
        self.assertTrue(user.is_staff)

    def test_username_siz_bir_nechta_user(self):
        User.objects.create_user('901112233', 'Parol123!', full_name='Ali', email='a@b.uz')
        User.objects.create_user('901112234', 'Parol123!', full_name='Vali', email='v@b.uz')
        self.assertEqual(User.objects.filter(username__isnull=True).count(), 2)

    def test_superuser(self):
        su = User.objects.create_superuser('901112233', 'Parol123!', full_name='Admin', email='s@b.uz')
        self.assertTrue(su.is_staff and su.is_superuser and su.is_active)
        self.assertEqual(su.role, UserRole.ADMIN)


class VerificationCodeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('901112233', 'Parol123!', full_name='Ali', email='a@b.uz')

    def test_kod_va_muddat(self):
        code = VerificationCode.objects.create(user=self.user, code=VerificationCode.generate_code())
        self.assertEqual(len(code.code), 6)
        self.assertTrue(code.is_valid)
        self.assertFalse(code.is_expired)

    def test_ishlatilgan_kod_yaroqsiz(self):
        code = VerificationCode.objects.create(user=self.user, code='123456', is_used=True)
        self.assertFalse(code.is_valid)

    def test_urinishlar_tugasa_yaroqsiz(self):
        code = VerificationCode.objects.create(user=self.user, code='123456')
        code.attempts = code.max_attempts
        self.assertFalse(code.is_valid)


class RegisterAPITests(APITestCase):
    url = reverse_lazy('users:register')

    def payload(self, **over):
        data = {
            'full_name': 'Ali Valiyev',
            'phone_number': '901112233',
            'email': 'ali@mail.uz',
            'password': 'Qwerty!2345',
        }
        data.update(over)
        return data

    def test_royxatdan_otish(self):
        response = self.client.post(self.url, self.payload(), format='json')
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email='ali@mail.uz')
        self.assertEqual(user.phone_number, VALID)      # normalizatsiya qilindi
        self.assertEqual(user.role, UserRole.USER)      # hamma oddiy user
        self.assertFalse(user.is_active)                # tasdiqlashdan oldin faol emas
        self.assertTrue(user.check_password('Qwerty!2345'))
        self.assertNotIn('password', response.data['user'])

    def test_role_va_is_active_tashqaridan_berilmaydi(self):
        response = self.client.post(
            self.url,
            self.payload(role='admin', is_active=True, is_superuser=True),
            format='json',
        )
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email='ali@mail.uz')
        self.assertEqual(user.role, UserRole.USER)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_superuser)

    def test_dublikat_raqam_boshqa_formatda(self):
        self.client.post(self.url, self.payload(), format='json')
        response = self.client.post(
            self.url,
            self.payload(phone_number='+998 90 111 22 33', email='vali@mail.uz'),
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('phone_number', response.data)

    def test_notogri_raqam_va_zaif_parol(self):
        response = self.client.post(
            self.url, self.payload(phone_number='123', password='12345678'), format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('phone_number', response.data)
        self.assertIn('password', response.data)


class MeAPITests(APITestCase):
    url = reverse_lazy('users:me')

    def setUp(self):
        self.user = User.objects.create_user(
            '901112233', 'Qwerty!2345', full_name='Ali', email='ali@mail.uz'
        )

    def test_token_siz_401(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_faol_bolmagan_user_token_ololmaydi(self):
        response = self.client.post(
            reverse_lazy('users:token_obtain_pair'),
            {'phone_number': '901112233', 'password': 'Qwerty!2345'},
            format='json',
        )
        self.assertEqual(response.status_code, 401)

    def test_token_bilan_oz_profilini_oladi(self):
        User.objects.filter(pk=self.user.pk).update(is_active=True)
        token = self.client.post(
            reverse_lazy('users:token_obtain_pair'),
            {'phone_number': '901112233', 'password': 'Qwerty!2345'},
            format='json',
        ).data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.user.pk)
        self.assertEqual(response.data['phone_number'], VALID)
        self.assertNotIn('password', response.data)
