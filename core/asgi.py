"""
DIQQAT: Bu fayl loyihangiz ILDIZIDAGI (settings.py bilan bir joyda turgan)
asgi.py faylini TO'LIQ ALMASHTIRISH uchun emas — balki shu fayldagi
mavjud "django_asgi_app" qismini saqlab, pastdagi WebSocket qismini
QO'SHISH uchun namuna.

Odatda bu fayl config/asgi.py yoki <loyiha_nomi>/asgi.py da turadi.
"DJANGO_SETTINGS_MODULE" qatoridagi "config.settings" qismini
o'zingizning haqiqiy settings yo'lingizga almashtiring.

O'ZGARISH: oddiy "AuthMiddlewareStack" o'rniga "JWTAuthMiddlewareStack"
ishlatildi. Sabab: AuthMiddlewareStack faqat Django SESSION/COOKIE orqali
autentifikatsiya qiladi, lekin frontend React SPA JWT access_token'ni
localStorage'da saqlaydi va WebSocket ulanishda uni faqat
"?token=<access_token>" query-param orqali yubora oladi (brauzer
WebSocket API'si maxsus header qo'shishga imkon bermaydi). Shu sababli
"apps/live_speaking/ws_auth_middleware.py" ichidagi JWTAuthMiddlewareStack
o'sha query-paramni o'qib, scope['user']ni to'g'ri o'rnatadi - aks holda
consumers.py dagi "self.user.is_authenticated" doim False bo'lib, har bir
ulanish 4001 kodi bilan yopilib qolar edi.
"""

import os

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # <-- moslang
django.setup()

django_asgi_app = get_asgi_application()

from apps.live_speaking.routing import websocket_urlpatterns  # noqa: E402
from apps.live_speaking.ws_auth_middleware import JWTAuthMiddlewareStack  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})