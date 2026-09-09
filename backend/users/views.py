"""users app view'lari."""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ — ochiq.

    User `role='user'` va `is_active=False` holatida yaratiladi.
    Faollashtirish keyingi bosqichda (Telegram bot + /auth/confirm/) qo'shiladi.
    """

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


class MeView(generics.RetrieveAPIView):
    """GET /api/v1/auth/me/ — faqat tizimga kirgan user uchun."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
