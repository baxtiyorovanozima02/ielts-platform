from django.contrib import admin
from django.utils.html import format_html
from .models import SubscriptionPlan, Subscription, Payment
from .tasks import notify_payment_confirmed, notify_payment_rejected


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'duration_days', 'is_active']
    list_filter = ['plan_type', 'is_active']
    search_fields = ['name']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'started_at', 'expires_at', 'is_active']
    list_filter = ['status', 'is_active']
    search_fields = ['user__username']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount', 'payment_method', 'status', 'created_at', 'screenshot_preview']
    list_filter = ['status', 'payment_method']
    search_fields = ['user__username', 'transaction_id']
    readonly_fields = ['created_at', 'confirmed_at', 'screenshot_preview']
    actions = ['confirm_payments', 'reject_payments']

    def screenshot_preview(self, obj):
        if obj.screenshot:
            return format_html('<a href="{}" target="_blank">Ko\'rish</a>', obj.screenshot.url)
        return "Yo'q"
    screenshot_preview.short_description = "Chek"

    def confirm_payments(self, request, queryset):
        for payment in queryset.filter(status='pending'):
            payment.confirm()
            notify_payment_confirmed.delay(payment.id)
        self.message_user(request, "Tanlangan to'lovlar tasdiqlandi!")
    confirm_payments.short_description = "✅ Tasdiqlash"

    def reject_payments(self, request, queryset):
        for payment in queryset.filter(status='pending'):
            payment.reject()
            notify_payment_rejected.delay(payment.id)
        self.message_user(request, "Tanlangan to'lovlar rad etildi!")
    reject_payments.short_description = "❌ Rad etish"