"""
users app modellari.

TZ 3.2 (User) va 3.3 (VerificationCode) bo'yicha yozilgan.
Login `phone_number` orqali amalga oshadi — `username` majburiy emas.
"""

import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from .utils import PhoneNumberField, normalize_phone


class UserRole(models.TextChoices):
    USER = 'user', 'Foydalanuvchi'
    ADMIN = 'admin', 'Administrator'


class UserManager(BaseUserManager):
    """`phone_number` ustidan ishlaydigan manager (TZ S1-01)."""

    use_in_migrations = True

    def _create_user(self, phone_number, password, **extra_fields):
        if not phone_number:
            raise ValueError("Telefon raqam majburiy.")
        phone_number = normalize_phone(phone_number)
        email = extra_fields.pop('email', None)
        if email:
            email = self.normalize_email(email)
        user = self.model(phone_number=phone_number, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('role', UserRole.USER)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        # Ro'yxatdan o'tgan user kod tasdiqlanmaguncha faol emas (TZ 4-bo'lim)
        extra_fields.setdefault('is_active', False)
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('role', UserRole.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser uchun is_staff=True bo'lishi shart.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser uchun is_superuser=True bo'lishi shart.")

        return self._create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Loyihaning asosiy foydalanuvchi modeli (TZ 3.2)."""

    full_name = models.CharField("F.I.Sh.", max_length=150)
    username = models.CharField(
        "Username",
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        help_text="Ixtiyoriy. Login uchun emas — login telefon raqam orqali.",
    )
    phone_number = PhoneNumberField(
        "Telefon raqam",
        unique=True,
        help_text=(
            "901112233, 998901112233 yoki +998 90 111 22 33 — "
            "bazada +998901112233 ko'rinishida saqlanadi."
        ),
    )
    email = models.EmailField("Email", unique=True)

    bio = models.TextField("Bio", blank=True)
    avatar = models.ImageField("Avatar", upload_to='avatars/', null=True, blank=True)

    role = models.CharField(
        "Rol",
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.USER,
    )

    is_active = models.BooleanField(
        "Faol",
        default=False,
        help_text="Telegram bot orqali kod tasdiqlangandan keyin True bo'ladi.",
    )
    is_staff = models.BooleanField("Xodim (admin panel)", default=False)

    telegram_id = models.BigIntegerField(
        "Telegram ID",
        null=True,
        blank=True,
        db_index=True,
        help_text="Botga /start bosganda yoziladi.",
    )
    last_login_at = models.DateTimeField("Oxirgi kirish", null=True, blank=True)

    created_at = models.DateTimeField("Yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("Yangilangan", auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name', 'email']

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['role', 'is_active']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"

    def save(self, *args, **kwargs):
        # Raqam har qanday yo'ldan kelsa ham bitta formatga keltiriladi (TZ S1-02)
        self.phone_number = normalize_phone(self.phone_number)
        # TZ S1-13: role='admin' bo'lsa admin panelga kira olsin
        if self.role == UserRole.ADMIN:
            self.is_staff = True
        # Bo'sh username unique cheklovga tushmasligi uchun NULL ga aylantiriladi
        if not self.username:
            self.username = None
        super().save(*args, **kwargs)

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN


class CodePurpose(models.TextChoices):
    REGISTER = 'register', "Ro'yxatdan o'tish"
    RESET_PASSWORD = 'reset_password', "Parolni tiklash"


def default_expires_at():
    """Kod amal qilish muddati — sozlamadagi TTL (default 5 daqiqa)."""
    minutes = getattr(settings, 'VERIFICATION_CODE_TTL_MINUTES', 5)
    return timezone.now() + timedelta(minutes=minutes)


class VerificationCode(models.Model):
    """Telegram bot orqali yuboriladigan tasdiqlash kodi (TZ 3.3)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='codes',
        verbose_name="Foydalanuvchi",
    )
    code = models.CharField("Kod", max_length=6)
    purpose = models.CharField(
        "Maqsad",
        max_length=20,
        choices=CodePurpose.choices,
        default=CodePurpose.REGISTER,
    )
    is_used = models.BooleanField("Ishlatilgan", default=False)
    attempts = models.PositiveSmallIntegerField("Urinishlar soni", default=0)
    expires_at = models.DateTimeField("Amal qilish muddati", default=default_expires_at)
    created_at = models.DateTimeField("Yaratilgan", auto_now_add=True)

    class Meta:
        verbose_name = "Tasdiqlash kodi"
        verbose_name_plural = "Tasdiqlash kodlari"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'purpose', 'is_used']),
        ]

    def __str__(self):
        return f"{self.user.phone_number} — {self.get_purpose_display()}"

    @staticmethod
    def generate_code():
        length = getattr(settings, 'VERIFICATION_CODE_LENGTH', 6)
        return str(random.randint(10 ** (length - 1), 10**length - 1))

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def max_attempts(self):
        return getattr(settings, 'VERIFICATION_CODE_MAX_ATTEMPTS', 5)

    @property
    def is_valid(self):
        """Kod hali ishlatilmagan, muddati o'tmagan va urinishlar tugamagan."""
        return not self.is_used and not self.is_expired and self.attempts < self.max_attempts
