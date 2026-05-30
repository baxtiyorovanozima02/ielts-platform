from django.contrib import admin
from .models import User, TelegramOTP


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'phone_number', 'is_premium')


@admin.register(TelegramOTP)
class TelegramOTPAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'otp_code', 'is_used', 'created_at')