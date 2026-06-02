from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
    ]

    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(default=30)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.price} UZS"


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

    def is_expired(self):
        return timezone.now() > self.expires_at


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]

    PAYMENT_METHODS = [
        ('payme', 'Payme'),
        ('click', 'Click'),
        ('transfer', 'Bank transfer'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='payme')
    transaction_id = models.CharField(max_length=100, blank=True)
    screenshot = models.ImageField(upload_to='payment_screenshots/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} UZS - {self.status}"

    def confirm(self, admin_note=''):
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.note = admin_note
        self.save()

        Subscription.objects.filter(
            user=self.user,
            is_active=True
        ).update(is_active=False, status='cancelled')

        expires_at = timezone.now() + timedelta(days=self.plan.duration_days)
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            expires_at=expires_at,
            is_active=True
        )

        self.user.is_premium = True
        self.user.save()

        return subscription

    def reject(self, admin_note=''):
        self.status = 'rejected'
        self.note = admin_note
        self.save()