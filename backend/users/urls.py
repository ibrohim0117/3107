"""users app URL'lari — bazasi: /api/v1/auth/"""

from django.urls import path

from .views import MeView, RegisterView, TokenObtainView, TokenRefreshCustomView

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', MeView.as_view(), name='me'),

    # Vaqtinchalik — TZ S1-09 dagi custom /auth/login/ bilan almashtiriladi
    path('token/', TokenObtainView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshCustomView.as_view(), name='token_refresh'),
]
