from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, TelegramOTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'phone_number', 'is_premium', 'xp_total', 'streak_count', 'is_staff', 'date_joined')
    list_filter = ('is_premium', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('-date_joined',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('SelfStudy.uz', {
            'fields': ('phone_number', 'is_premium', 'xp_total', 'streak_count')
        }),
    )


@admin.register(TelegramOTP)
class TelegramOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'is_used', 'created_at')
    list_filter = ('is_used',)
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)