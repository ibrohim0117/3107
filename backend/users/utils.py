"""
Telefon raqam bilan ishlash utillari (TZ S1-02).

Bazada raqam DOIM bitta formatda saqlanadi: +998901112233
Foydalanuvchi esa qulay ko'rinishda kiritishi mumkin:
    901112233
    90 111 22 33
    998901112233
    +998 (90) 111-22-33
    00998901112233
"""

import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

PHONE_ERROR_MESSAGE = (
    "Telefon raqam noto'g'ri. Namuna: +998901112233, 998901112233 yoki 901112233"
)

# Normalizatsiyadan keyingi yagona format — oxirgi nazorat
phone_validator = RegexValidator(
    regex=r'^\+998\d{9}$',
    message=PHONE_ERROR_MESSAGE,
)


def normalize_phone(value):
    """Har xil formatdagi raqamni `+998XXXXXXXXX` ko'rinishiga keltiradi.

    Bo'sh qiymat o'zgarishsiz qaytadi — majburiylikni model maydoni tekshiradi.
    Noto'g'ri raqamda `ValidationError` ko'tariladi.
    """
    if value in (None, ''):
        return value

    # Faqat raqamlarni qoldiramiz: bo'shliq, qavs, chiziqcha, "+" tashlanadi
    digits = re.sub(r'\D', '', str(value))

    # Xalqaro prefiks 00998... ko'rinishida kelsa
    if digits.startswith('00'):
        digits = digits[2:]

    if len(digits) == 9:
        # Operator kodidan boshlangan lokal format: 901112233
        digits = '998' + digits
    elif len(digits) == 12 and digits.startswith('998'):
        # 998901112233
        pass
    else:
        raise ValidationError(PHONE_ERROR_MESSAGE, code='invalid_phone')

    return '+' + digits


class PhoneNumberField(models.CharField):
    """Qiymat validatsiyadan OLDIN normalizatsiya qilinadigan CharField.

    `to_python` `full_clean()` ichida validatorlardan oldin chaqiriladi,
    shuning uchun serializer/forma/admin/`createsuperuser` — hammasi
    bir xil qoidaga bo'ysunadi.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 13)
        super().__init__(*args, **kwargs)
        self.validators.append(phone_validator)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if kwargs.get('max_length') == 13:
            del kwargs['max_length']
        return name, path, args, kwargs

    def to_python(self, value):
        return normalize_phone(super().to_python(value))
