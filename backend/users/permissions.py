"""Rolga asoslangan permission klasslari (TZ 6.4)."""

from rest_framework.permissions import BasePermission

from .models import UserRole


class IsAdminRole(BasePermission):
    """Faqat akkaunti tasdiqlangan (`is_active=True`) va `role='admin'` bo'lgan user.

    DRF'ning `IsAdminUser` i `is_staff` ga qaraydi — bizda esa rol `role`
    maydonida, shuning uchun alohida permission.
    """

    message = "Bu amalni faqat akkaunti tasdiqlangan admin bajara oladi."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.role == UserRole.ADMIN
        )
