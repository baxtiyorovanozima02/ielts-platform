"""
HeyGen Streaming Avatar bilan ishlash uchun yordamchi funksiyalar.

Ishlash mantiqi:
1. Backend (biz) HeyGen API'ga so'rov yuboradi va qisqa muddatli "session token" oladi.
2. Bu tokenni frontendga beramiz.
3. Frontend HeyGen'ning tayyor JS SDK'si (@heygen/streaming-avatar) orqali
   to'g'ridan-to'g'ri HeyGen serverlariga ulanadi va video+audio oqimini
   o'zi boshqaradi (WebRTC ulanishini o'zimiz yozishimiz shart emas).

Hujjat: https://docs.heygen.com/reference/streaming-avatar-sdk-overview
(API tafsilotlari o'zgarishi mumkin, eng so'nggi holatini HeyGen dashboard/hujjatidan tekshiring)
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

HEYGEN_CREATE_TOKEN_URL = "https://api.heygen.com/v1/streaming.create_token"


class AvatarServiceError(Exception):
    """Avatar xizmati bilan bog'liq har qanday xatolik uchun umumiy klass."""
    pass


def create_avatar_session_token() -> str:
    """
    HeyGen'dan bir martalik (qisqa muddatli) streaming session token oladi.
    Frontend shu tokenni HeyGen SDK'siga berib, avatar bilan video ulanish o'rnatadi.
    """
    headers = {
        "X-Api-Key": settings.HEYGEN_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(HEYGEN_CREATE_TOKEN_URL, headers=headers, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.exception("HeyGen token olishda xatolik: %s", exc)
        raise AvatarServiceError("Avatar xizmatiga ulanib bo'lmadi") from exc

    data = response.json()
    token = data.get("data", {}).get("token")

    if not token:
        logger.error("HeyGen javobida token topilmadi: %s", data)
        raise AvatarServiceError("Avatar tokeni olinmadi")

    return token


def get_avatar_id_for_voice(voice) -> str:
    """
    ExaminerVoice modeliga bog'langan HeyGen avatar_id'ni qaytaradi.
    Agar voice tanlanmagan yoki avatar_id bo'sh bo'lsa, standart avatarga tushadi.
    """
    if voice and getattr(voice, 'avatar_id', None):
        return voice.avatar_id
    return settings.HEYGEN_DEFAULT_AVATAR_ID