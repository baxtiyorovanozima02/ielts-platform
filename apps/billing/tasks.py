from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import requests


def send_telegram_message(telegram_id, message):
    """Telegram botdan xabar yuborish"""
    token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={
        'chat_id': telegram_id,
        'text': message,
        'parse_mode': 'Markdown'
    })


@shared_task
def notify_payment_received(payment_id):
    """Foydalanuvchi to'lov qilganda xabar yuborish"""
    from .models import Payment
    from apps.users.models import TelegramOTP

    payment = Payment.objects.get(id=payment_id)
    user = payment.user

    if user.email:
        send_mail(
            subject="To'lovingiz qabul qilindi",
            message=f"""
Assalomu alaykum, {user.username}!

Sizning to'lovingiz qabul qilindi va tekshirilmoqda.

To'lov ma'lumotlari:
- Plan: {payment.plan.name}
- Summa: {payment.amount} UZS
- To'lov usuli: {payment.payment_method}
- Holat: Kutilmoqda

Admin tasdiqlagan zahoti obunangiz faollashadi.

IELTS Platform
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

    otp = TelegramOTP.objects.filter(user=user).order_by('-created_at').first()
    if otp and otp.telegram_id:
        send_telegram_message(
            otp.telegram_id,
            f"✅ *To'lovingiz qabul qilindi!*\n\n"
            f"📦 Plan: {payment.plan.name}\n"
            f"💰 Summa: {payment.amount} UZS\n"
            f"⏳ Holat: Tekshirilmoqda...\n\n"
            f"Admin tasdiqlagan zahoti xabar beramiz!"
        )


@shared_task
def notify_payment_confirmed(payment_id):
    """Admin to'lovni tasdiqlaganda xabar yuborish"""
    from .models import Payment
    from apps.users.models import TelegramOTP

    payment = Payment.objects.get(id=payment_id)
    user = payment.user

    if user.email:
        send_mail(
            subject="🎉 Obunangiz faollashdi!",
            message=f"""
Assalomu alaykum, {user.username}!

Tabriklaymiz! Sizning {payment.plan.name} obunangiz muvaffaqiyatli faollashdi.

Obuna ma'lumotlari:
- Plan: {payment.plan.name}
- Muddat: {payment.plan.duration_days} kun
- Summa: {payment.amount} UZS

Barcha premium imkoniyatlardan foydalaning!

IELTS Platform
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

    otp = TelegramOTP.objects.filter(user=user).order_by('-created_at').first()
    if otp and otp.telegram_id:
        send_telegram_message(
            otp.telegram_id,
            f"🎉 *Obunangiz faollashdi!*\n\n"
            f"📦 Plan: *{payment.plan.name}*\n"
            f"📅 Muddat: {payment.plan.duration_days} kun\n"
            f"💰 Summa: {payment.amount} UZS\n\n"
            f"Barcha premium imkoniyatlardan foydalaning! 🚀"
        )


@shared_task
def notify_payment_rejected(payment_id):
    """Admin to'lovni rad etganda xabar yuborish"""
    from .models import Payment
    from apps.users.models import TelegramOTP

    payment = Payment.objects.get(id=payment_id)
    user = payment.user

    if user.email:
        send_mail(
            subject="To'lov rad etildi",
            message=f"""
Assalomu alaykum, {user.username}!

Afsuski, sizning to'lovingiz rad etildi.

Sabab: {payment.note if payment.note else "Ko'rsatilmagan"}

Iltimos, qayta urinib ko'ring yoki biz bilan bog'laning.

IELTS Platform
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

    otp = TelegramOTP.objects.filter(user=user).order_by('-created_at').first()
    if otp and otp.telegram_id:
        send_telegram_message(
            otp.telegram_id,
            f"❌ *To'lovingiz rad etildi*\n\n"
            f"📝 Sabab: {payment.note if payment.note else 'Korsatilmagan'}\n\n"
            f"Qayta urinib ko'ring yoki admin bilan bog'laning."
        )


@shared_task
def check_expired_subscriptions():
    """Har kuni tugagan obunalarni tekshirish — Celery beat bilan ishlaydi"""
    from .models import Subscription
    from django.utils import timezone

    expired = Subscription.objects.filter(
        is_active=True,
        expires_at__lt=timezone.now()
    )

    for subscription in expired:
        subscription.is_active = False
        subscription.status = 'expired'
        subscription.save()

        subscription.user.is_premium = False
        subscription.user.save()

        # Foydalanuvchiga xabar
        notify_payment_received.delay(subscription.user.id)