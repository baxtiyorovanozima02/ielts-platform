"""
Channels (WebSocket) so'rovlarini JWT token bilan autentifikatsiya qilish uchun middleware.

Nega kerak?
-----------
Oddiy HTTP so'rovlarda frontend "Authorization: Bearer <token>" headerini yuboradi,
lekin brauzerning native WebSocket API'si maxsus headerlar qo'shishga imkon bermaydi.
Shuning uchun frontend tokenni URL query-param sifatida yuboradi:

    wss://example.com/ws/live-speaking/5/?token=<access_token>

Bu middleware shu query-paramdagi tokenni o'qiydi, simplejwt yordamida tekshiradi
va scope['user']ga tegishli foydalanuvchini joylashtiradi. Shundan keyingina
`consumers.py` ichidagi `self.scope.get('user')` to'g'ri ishlaydi.

O'rnatish
---------
pip install djangorestframework-simplejwt   # agar hali o'rnatilmagan bo'lsa

Ulash (loyihangizning asgi.py faylida, misol quyida - asgi_example.py):
    from apps.live_speaking.ws_auth_middleware import JWTAuthMiddlewareStack
    application = ProtocolTypeRouter({
        "websocket": JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    })
"""

from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def get_user_from_token(token_str):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        access_token = AccessToken(token_str)
        user_id = access_token['user_id']
        return User.objects.get(id=user_id)
    except (InvalidToken, TokenError, KeyError, User.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware:
    """
    ASGI middleware: `?token=...` query-paramdan JWT'ni o'qib, scope['user']ni
    o'sha foydalanuvchiga o'rnatadi. Token bo'lmasa yoki noto'g'ri bo'lsa,
    AnonymousUser qoladi (consumer o'zi 4001 bilan ulanishni yopadi).
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token_list = query_params.get('token')

        if token_list:
            scope['user'] = await get_user_from_token(token_list[0])
        else:
            scope['user'] = AnonymousUser()

        return await self.app(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """
    JWTAuthMiddleware'ni Channelsning standart AuthMiddlewareStack bilan birlashtiradi,
    shunda session-based auth ham, JWT query-param auth ham ishlaydi.
    """
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))