"""users app view'lari."""

from django.db import transaction
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    ConfirmResponseSerializer,
    ConfirmSerializer,
    RegisterResponseSerializer,
    RegisterSerializer,
    UserSerializer,
)


@extend_schema(
    tags=['auth'],
    summary="Ro'yxatdan o'tish",
    description=(
        "Yangi foydalanuvchi yaratadi.\n\n"
        "- Hamma `role='user'` bilan ro'yxatdan o'tadi — `role`, `is_active`, "
        "`is_superuser` maydonlari so'rovda berilsa e'tiborsiz qoldiriladi.\n"
        "- Akkaunt `is_active=False` holatida yaratiladi, ya'ni darhol token ololmaydi.\n"
        "- Telefon raqam har qanday formatda yuborilishi mumkin, bazada "
        "`+998901112233` ko'rinishida saqlanadi."
    ),
    responses={201: RegisterResponseSerializer},
    examples=[
        OpenApiExample(
            "Minimal so'rov",
            request_only=True,
            value={
                'full_name': 'Ali Valiyev',
                'phone_number': '901112233',
                'email': 'ali@mail.uz',
                'password': 'Qwerty!2345',
            },
        ),
        OpenApiExample(
            "Telefon raqam boshqa formatda",
            request_only=True,
            value={
                'full_name': 'Vali Aliyev',
                'phone_number': '+998 90 111 22 34',
                'email': 'vali@mail.uz',
                'password': 'Qwerty!2345',
                'bio': "O'zim haqimda",
            },
        ),
        OpenApiExample(
            "Xatolik — raqam band",
            response_only=True,
            status_codes=['400'],
            value={'phone_number': ["Bu raqam allaqachon ro'yxatdan o'tgan."]},
        ),
    ],
)
class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ — ochiq."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'message': (
                    "Ro'yxatdan o'tdingiz. Akkaunt hozircha faol emas — "
                    "tasdiqlashdan keyin tizimga kira olasiz."
                ),
                'user': UserSerializer(user, context=self.get_serializer_context()).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=['auth'],
    summary="Akkauntni tasdiqlash",
    responses={200: ConfirmResponseSerializer},
    examples=[
        OpenApiExample(
            "So'rov",
            request_only=True,
            value={'phone_number': '901112233', 'code': '123456'},
        ),
        OpenApiExample(
            "Xatolik — kod noto'g'ri",
            response_only=True,
            status_codes=['400'],
            value={'code': ["Kod noto'g'ri. 2 ta urinish qoldi."]},
        ),
    ],
)
class ConfirmView(generics.GenericAPIView):
    """POST /api/v1/auth/confirm/ — ochiq."""

    serializer_class = ConfirmSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        code = serializer.validated_data['verification_code']

        with transaction.atomic():
            code.is_used = True
            code.save(update_fields=['is_used'])
            user.is_active = True
            user.save(update_fields=['is_active'])

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'message': "Akkaunt tasdiqlandi.",
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user, context=self.get_serializer_context()).data,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=['auth'],
    summary="Mening profilim",
    description=(
        "Tizimga kirgan foydalanuvchining o'z profili.\n\n"
        "`Authorization: Bearer <access>` sarlavhasi majburiy — aks holda `401`."
    ),
)
class MeView(generics.RetrieveAPIView):
    """GET /api/v1/auth/me/ — faqat tizimga kirgan user uchun."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# --- Vaqtinchalik JWT view'lari -------------------------------------------
# TZ S1-09/S1-10 da o'zbekcha xatoliklarga ega custom /auth/login/ va
# /auth/logout/ bilan almashtiriladi. Hozircha simplejwt'ning tayyorlari.

@extend_schema(
    tags=['auth'],
    summary="Token olish (vaqtinchalik)",
    description=(
        "Telefon raqam va parol evaziga `access` + `refresh` token qaytaradi.\n\n"
        "Akkaunt `is_active=False` bo'lsa `401` qaytadi."
    ),
)
class TokenObtainView(TokenObtainPairView):
    pass


@extend_schema(
    tags=['auth'],
    summary="Access tokenni yangilash (vaqtinchalik)",
    description=(
        "`refresh` token evaziga yangi `access` beradi.\n\n"
        "Rotatsiya yoqilgan: eski `refresh` blacklist'ga tushadi va qayta ishlamaydi."
    ),
)
class TokenRefreshCustomView(TokenRefreshView):
    pass
