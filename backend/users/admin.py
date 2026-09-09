"""
users app uchun Django admin sozlamalari (TZ S5-12).

Rol shu yerdan qo'lda o'zgartiriladi: role='admin' → is_staff avtomatik True.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import BaseUserCreationForm, UserChangeForm
from django.utils.html import format_html

from .models import User, VerificationCode


class UserCreationForm(BaseUserCreationForm):
    """Standart forma `username` so'raydi — bizda login `phone_number`."""

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ('phone_number', 'full_name', 'email')


class UserUpdateForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserUpdateForm

    list_display = (
        'phone_number',
        'full_name',
        'email',
        'role',
        'is_active',
        'is_staff',
        'telegram_badge',
        'created_at',
    )
    list_display_links = ('phone_number', 'full_name')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('phone_number', 'full_name', 'email', 'username', 'telegram_id')
    ordering = ('-created_at',)
    list_per_page = 25

    readonly_fields = ('last_login', 'last_login_at', 'created_at', 'updated_at', 'avatar_preview')

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ("Shaxsiy ma'lumot", {
            'fields': ('full_name', 'username', 'email', 'bio', 'avatar', 'avatar_preview'),
        }),
        ("Telegram", {'fields': ('telegram_id',)}),
        ("Ruxsatlar", {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': "role='admin' saqlansa is_staff avtomatik True bo'ladi.",
        }),
        ("Sanalar", {
            'fields': ('last_login', 'last_login_at', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'full_name', 'email', 'password1', 'password2'),
        }),
        ("Ruxsatlar", {'fields': ('role', 'is_active')}),
    )

    filter_horizontal = ('groups', 'user_permissions')

    @admin.display(description="Telegram", boolean=True)
    def telegram_badge(self, obj):
        return obj.telegram_id is not None

    @admin.display(description="Avatar")
    def avatar_preview(self, obj):
        if not obj.avatar:
            return "—"
        return format_html(
            '<img src="{}" style="max-height:120px;border-radius:8px;" />', obj.avatar.url
        )


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'purpose', 'is_used', 'attempts', 'expires_at', 'status')
    list_filter = ('purpose', 'is_used', 'created_at')
    search_fields = ('user__phone_number', 'user__full_name', 'code')
    ordering = ('-created_at',)
    list_select_related = ('user',)
    list_per_page = 50
    readonly_fields = ('user', 'code', 'purpose', 'attempts', 'expires_at', 'created_at')

    @admin.display(description="Holati")
    def status(self, obj):
        if obj.is_used:
            return "Ishlatilgan"
        if obj.is_expired:
            return "Muddati o'tgan"
        if obj.attempts >= obj.max_attempts:
            return "Bloklangan"
        return "Yaroqli"

    def has_add_permission(self, request):
        # Kod faqat bot/service orqali yaratiladi
        return False
