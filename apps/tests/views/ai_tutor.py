
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import requests
import logging

logger = logging.getLogger(__name__)

XAI_URL = "https://api.x.ai/v1/chat/completions"
XAI_MODEL = "grok-4-fast"
MAX_MESSAGES = 20
REQUEST_TIMEOUT = 60

SYSTEM_PROMPT = """You are an expert IELTS tutor. Help the student prepare for their IELTS exam.
You can:
- Give writing feedback and tips
- Explain grammar rules with examples
- Provide speaking practice questions
- Give vocabulary advice
- Explain IELTS band scoring criteria
- Answer questions about the IELTS test format

Be encouraging, specific, and practical. Use examples. Keep responses concise but helpful.
If the student writes in Uzbek, respond in Uzbek. If in English, respond in English."""


class AIChatView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="AI Tutor chat",
        operation_description="Frontend xabarlarni yuboradi, backend OpenRouter orqali javob qaytaradi.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["messages"],
            properties={
                "messages": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "role": openapi.Schema(type=openapi.TYPE_STRING),
                            "content": openapi.Schema(type=openapi.TYPE_STRING),
                        },
                    ),
                    description="Suhbat tarixi (role: user | assistant)",
                ),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "reply": openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        },
    )
    def post(self, request):
        messages = request.data.get("messages", [])

        if not messages or not isinstance(messages, list):
            return Response(
                {"error": "messages array required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sanitized = [
            {"role": m["role"], "content": str(m["content"])[:4000]}
            for m in messages[-MAX_MESSAGES:]
            if isinstance(m, dict)
            and m.get("role") in ("user", "assistant")
            and m.get("content")
        ]

        if not sanitized:
            return Response(
                {"error": "No valid messages provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        headers = {
            "Authorization": f"Bearer {settings.XAI_API_KEY}",
            "Content-Type": "application/json",
        }
        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}] + sanitized

        try:
            response = requests.post(
                XAI_URL,
                headers=headers,
                json={
                    "model": XAI_MODEL,
                    "messages": messages_payload,
                    "max_tokens": 800,
                },
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            return Response({"reply": reply, "model_used": XAI_MODEL})

        except requests.Timeout:
            logger.warning("xAI timeout for user %s", request.user.id)
            return Response(
                {"error": "AI javob berish vaqti tugadi. Qayta urinib ko'ring."},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.error("xAI request error for user %s: %s", request.user.id, exc)
            return Response(
                {"error": "AI xizmatiga ulanishda xatolik yuz berdi."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except (KeyError, IndexError) as exc:
            logger.error("xAI unexpected response: %s", exc)
            return Response(
                {"error": "AI dan kutilmagan javob keldi."},
                status=status.HTTP_502_BAD_GATEWAY,
            )