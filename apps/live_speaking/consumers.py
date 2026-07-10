import base64
import json
import logging

import requests
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

from .models import LiveSpeakingSession, LiveSpeakingMessage

logger = logging.getLogger(__name__)

GROQ_TRANSCRIPTION_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_CHAT_MODEL = "llama-3.3-70b-versatile"

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

SYSTEM_PROMPT = """You are a friendly IELTS speaking examiner having a live spoken
conversation with a student. Ask natural follow-up questions like a real examiner
(Part 1 style small talk unless told otherwise). Keep every reply SHORT (1-3
sentences) since it will be spoken out loud. Do not use markdown, bullet points,
or asterisks - plain spoken sentences only. If the student writes in Uzbek,
reply in English anyway (this is English speaking practice), but you can add a
short Uzbek clarification in parentheses only if the student seems completely lost."""


class LiveSpeakingConsumer(AsyncWebsocketConsumer):
    """
    Client bilan protokol:

    Clientdan keladigan xabarlar (JSON, text frame):
      {"type": "audio_chunk", "audio_base64": "..."}   -> audio bo'lakchasini bufferga qo'shadi
      {"type": "end_of_turn"}                          -> foydalanuvchi gapirib bo'ldi, javob tayyorlash boshlanadi

    Serverdan clientga ketadigan xabarlar (JSON):
      {"type": "status", "state": "listening|thinking|speaking"}
      {"type": "transcript", "text": "..."}             -> foydalanuvchi nima deganini STT aniqladi
      {"type": "assistant_text", "text": "..."}         -> AI javobi matn shaklida
      {"type": "assistant_audio", "audio_base64": "...", "mime": "audio/mpeg"}  -> AI javobi ovozi
      {"type": "error", "message": "..."}
    """

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.user = self.scope.get('user')
        self.audio_buffer = bytearray()

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.session = await self._get_session(self.session_id, self.user)
        if not self.session:
            await self.close(code=4004)
            return

        await self.accept()
        await self._set_session_status('active')
        await self.send_json({"type": "status", "state": "listening"})

    async def disconnect(self, close_code):
        if getattr(self, 'session', None):
            await self._set_session_status('ended')

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json({"type": "error", "message": "Noto'g'ri JSON formati"})
            return

        msg_type = data.get('type')

        if msg_type == 'audio_chunk':
            chunk_b64 = data.get('audio_base64', '')
            try:
                self.audio_buffer.extend(base64.b64decode(chunk_b64))
            except Exception:
                await self.send_json({"type": "error", "message": "Audio chunkni o'qib bo'lmadi"})
            return

        if msg_type == 'end_of_turn':
            await self._handle_end_of_turn()
            return

        await self.send_json({"type": "error", "message": f"Noma'lum xabar turi: {msg_type}"})

    async def _handle_end_of_turn(self):
        if not self.audio_buffer:
            await self.send_json({"type": "error", "message": "Audio kelmadi, qayta urinib ko'ring"})
            return

        await self.send_json({"type": "status", "state": "thinking"})

        audio_bytes = bytes(self.audio_buffer)
        self.audio_buffer = bytearray()

        try:
            transcript = await self._speech_to_text(audio_bytes)
        except Exception as exc:
            logger.exception("STT xatolik: %s", exc)
            await self.send_json({"type": "error", "message": "Ovozni matnga o'girishda xatolik"})
            await self.send_json({"type": "status", "state": "listening"})
            return

        if not transcript.strip():
            await self.send_json({"type": "error", "message": "Gap eshitilmadi, yana urinib ko'ring"})
            await self.send_json({"type": "status", "state": "listening"})
            return

        await self.send_json({"type": "transcript", "text": transcript})
        await self._save_message('user', transcript)

        try:
            reply_text = await self._get_ai_reply()
        except Exception as exc:
            logger.exception("LLM xatolik: %s", exc)
            await self.send_json({"type": "error", "message": "AI javob berishda xatolik"})
            await self.send_json({"type": "status", "state": "listening"})
            return

        await self.send_json({"type": "assistant_text", "text": reply_text})
        await self._save_message('assistant', reply_text)

        await self.send_json({"type": "status", "state": "speaking"})

        try:
            audio_reply_b64 = await self._text_to_speech(reply_text)
            await self.send_json({
                "type": "assistant_audio",
                "audio_base64": audio_reply_b64,
                "mime": "audio/mpeg",
            })
        except Exception as exc:
            logger.exception("TTS xatolik: %s", exc)
            await self.send_json({"type": "error", "message": "Ovoz yaratishda xatolik (matn tayyor)"})

        await self.send_json({"type": "status", "state": "listening"})

    async def _speech_to_text(self, audio_bytes: bytes) -> str:
        def _call():
            files = {'file': ('audio.webm', audio_bytes, 'audio/webm')}
            data = {'model': 'whisper-large-v3', 'response_format': 'text'}
            headers = {'Authorization': f'Bearer {settings.GROQ_API_KEY}'}
            resp = requests.post(GROQ_TRANSCRIPTION_URL, headers=headers, files=files, data=data, timeout=60)
            resp.raise_for_status()
            return resp.text.strip()

        return await sync_to_async(_call, thread_sensitive=False)()

    async def _get_ai_reply(self) -> str:
        history = await self._get_recent_messages()

        def _call():
            messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}] + history
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            }
            resp = requests.post(
                GROQ_CHAT_URL,
                headers=headers,
                json={"model": GROQ_CHAT_MODEL, "messages": messages_payload, "max_tokens": 200},
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()

        return await sync_to_async(_call, thread_sensitive=False)()

    async def _text_to_speech(self, text: str) -> str:
        voice_id = await self._get_voice_id()

        def _call():
            headers = {
                "xi-api-key": settings.ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            }
            payload = {
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            }
            url = ELEVENLABS_TTS_URL.format(voice_id=voice_id)
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            return base64.b64encode(resp.content).decode('utf-8')

        return await sync_to_async(_call, thread_sensitive=False)()

    @sync_to_async
    def _get_session(self, session_id, user):
        return LiveSpeakingSession.objects.filter(id=session_id, user=user).first()

    @sync_to_async
    def _set_session_status(self, new_status):
        from django.utils import timezone
        self.session.status = new_status
        if new_status == 'ended':
            self.session.ended_at = timezone.now()
            self.session.save(update_fields=['status', 'ended_at'])
        else:
            self.session.save(update_fields=['status'])

    @sync_to_async
    def _save_message(self, role, text):
        LiveSpeakingMessage.objects.create(session=self.session, role=role, text=text)

    @sync_to_async
    def _get_recent_messages(self):
        qs = self.session.messages.order_by('created_at').values('role', 'text')[:40]
        return [{"role": m['role'], "content": m['text']} for m in qs]

    @sync_to_async
    def _get_voice_id(self):
        if self.session.voice_id:
            return self.session.voice.tts_voice_id
        return settings.ELEVENLABS_DEFAULT_VOICE_ID

    async def send_json(self, data: dict):
        await self.send(text_data=json.dumps(data))