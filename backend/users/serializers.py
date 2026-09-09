"""users app serializerlari."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import F
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.validators import UniqueValidator

from .models import CodePurpose, User, VerificationCode
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
        user = User.objects.create_user(password=password, **validated_data)
        # Kod yaratiladi, lekin hech qayerga yuborilmaydi — admin paneldan ko'riladi
        user.create_code()
        return user


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


class ConfirmSerializer(serializers.Serializer):
    """POST /api/v1/auth/confirm/ — TZ 4.3.

    Kod to'g'ri bo'lsa `validated_data` ichiga `user` va `verification_code`
    qo'yiladi; akkauntni faollashtirish view'da bajariladi.
    """

    phone_number = PhoneField(max_length=13)
    code = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(phone_number=attrs['phone_number'])
        except User.DoesNotExist:
            raise NotFound("Bunday foydalanuvchi topilmadi.") from None

        if user.is_active:
            raise serializers.ValidationError(
                {'phone_number': "Akkaunt allaqachon tasdiqlangan."}
            )

        code = (
            user.codes.filter(purpose=CodePurpose.REGISTER, is_used=False)
            .order_by('-created_at')
            .first()
        )
        if code is None:
            raise serializers.ValidationError(
                {'code': "Tasdiqlash kodi topilmadi. Yangi kod so'rang."}
            )
        if code.is_expired:
            raise serializers.ValidationError(
                {'code': "Kod muddati tugagan. Yangi kod so'rang."}
            )
        if code.attempts >= code.max_attempts:
            raise serializers.ValidationError(
                {'code': "Urinishlar soni tugadi. Yangi kod so'rang."}
            )

        if code.code != attrs['code']:
            # Har xato urinish sanaladi (TZ 4.3)
            VerificationCode.objects.filter(pk=code.pk).update(attempts=F('attempts') + 1)
            left = code.max_attempts - (code.attempts + 1)
            message = (
                f"Kod noto'g'ri. {left} ta urinish qoldi."
                if left > 0
                else "Kod noto'g'ri. Urinishlar soni tugadi, yangi kod so'rang."
            )
            raise serializers.ValidationError({'code': message})

        attrs['user'] = user
        attrs['verification_code'] = code
        return attrs


class RegisterResponseSerializer(serializers.Serializer):
    """Faqat hujjat uchun — `POST /auth/register/` javobining tuzilishi."""

    message = serializers.CharField()
    user = UserSerializer()


class ConfirmResponseSerializer(serializers.Serializer):
    """Faqat hujjat uchun — `POST /auth/confirm/` javobining tuzilishi."""

    message = serializers.CharField()
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
