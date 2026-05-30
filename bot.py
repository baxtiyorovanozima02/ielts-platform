import os
import random
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from django.contrib.auth import get_user_model
from apps.users.models import TelegramOTP
from asgiref.sync import sync_to_async

User = get_user_model()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! IELTS Platform botiga xush kelibsiz!\n\n"
        "Ro'yxatdan o'tish uchun username ni yuboring:\n"
        "/otp <username>"
    )


async def send_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Foydalanish: /otp <username>")
        return

    username = context.args[0]
    telegram_id = str(update.effective_user.id)

    try:
        user = await sync_to_async(User.objects.get)(username=username)
    except User.DoesNotExist:
        await update.message.reply_text("Bu username topilmadi.")
        return

    otp_code = str(random.randint(100000, 999999))

    await sync_to_async(TelegramOTP.objects.create)(
        user=user,
        otp_code=otp_code,
        telegram_id=telegram_id
    )

    await update.message.reply_text(
        f"Tasdiqlash kodingiz: *{otp_code}*\n\nBu kod 5 daqiqa davomida amal qiladi.",
        parse_mode='Markdown'
    )

def run_bot():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('otp', send_otp))
    app.run_polling()


if __name__ == '__main__':
    run_bot()