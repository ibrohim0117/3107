"""users app serializerlari."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import User
from .utils import normalize_phone


class PhoneField(serializers.CharField):
    """Raqamni validatorlardan (jumladan unique) OLDIN normalizatsiya qiladi.

    Shu tufayli `901112233` va `+998901112233` bir xil raqam sifatida
    qaraladi va dublikat to'g'ri aniqlanadi.
    """

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        try:
            return normalize_phone(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc


class RegisterSerializer(serializers.ModelSerializer):
    """POST /api/v1/auth/register/ — TZ 4.1.

    Hamma oddiy `user` roli bilan ro'yxatdan o'tadi: `role` va `is_active`
    tashqaridan berilmaydi.
    """

    phone_number = PhoneField(
        max_length=13,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Bu raqam allaqachon ro'yxatdan o'tgan.",
            )
        ],
        help_text="901112233, 998901112233 yoki +998 90 111 22 33",
    )
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Bu email allaqachon ro'yxatdan o'tgan.",
            )
        ]
    )
    password = serializers.CharField(
        write_only=True,
        min_length=6,
        style={'input_type': 'password'},
        help_text="Kamida 6 belgi.",
    )

    class Meta:
        model = User
        fields = ('id', 'full_name', 'phone_number', 'email', 'password', 'bio', 'avatar')
        extra_kwargs = {
            'full_name': {'required': True, 'allow_blank': False},
            'bio': {'required': False},
            'avatar': {'required': False},
        }

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        # create_user role='user' va is_active=False ni o'zi qo'yadi (TZ 4-bo'lim)
        return User.objects.create_user(password=password, **validated_data)


class UserSerializer(serializers.ModelSerializer):
    """GET /api/v1/auth/me/ — profil ma'lumotlari."""

    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'full_name',
            'username',
            'phone_number',
            'email',
            'bio',
            'avatar',
            'role',
            'role_display',
            'is_active',
            'telegram_id',
            'last_login_at',
            'created_at',
        )
        read_only_fields = fields
