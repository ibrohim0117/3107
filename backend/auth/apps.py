from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth'
    # 'auth' label django.contrib.auth bilan to'qnashadi,
    # shuning uchun bu app'ga alohida label beriladi.
    # Modellarga murojaat: 'users.User', 'users.VerificationCode'
    label = 'users'
