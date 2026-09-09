"""users app URL'lari — bazasi: /api/v1/auth/"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import MeView, RegisterView

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', MeView.as_view(), name='me'),

    # Vaqtinchalik: JWT ni sinash uchun simplejwt'ning tayyor view'lari.
    # TZ S1-09 da o'zbekcha xatoliklarga ega custom /auth/login/ bilan almashtiriladi.
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
