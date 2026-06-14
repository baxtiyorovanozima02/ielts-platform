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

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]
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
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}] + sanitized

        last_error = None
        last_status = status.HTTP_502_BAD_GATEWAY

        for model in GROQ_MODELS:
            try:
                response = requests.post(
                    GROQ_URL,
                    headers=headers,
                    json={
                        "model": model,
                        "messages": messages_payload,
                        "max_tokens": 800,
                    },
                    timeout=REQUEST_TIMEOUT,
                )

                if response.status_code in (400, 404, 429, 503):
                    logger.warning(
                        "Groq model %s unavailable (status %s) for user %s, trying next model",
                        model, response.status_code, request.user.id,
                    )
                    last_error = f"model {model} -> {response.status_code} {response.text[:200]}"
                    last_status = status.HTTP_502_BAD_GATEWAY
                    continue

                response.raise_for_status()
                reply = response.json()["choices"][0]["message"]["content"]
                return Response({"reply": reply, "model_used": model})

            except requests.Timeout:
                logger.warning("Groq timeout (model %s) for user %s", model, request.user.id)
                last_error = f"model {model} -> timeout"
                last_status = status.HTTP_504_GATEWAY_TIMEOUT
                continue
            except requests.RequestException as exc:
                logger.warning("Groq request error (model %s) for user %s: %s", model, request.user.id, exc)
                last_error = f"model {model} -> {exc}"
                last_status = status.HTTP_502_BAD_GATEWAY
                continue
            except (KeyError, IndexError) as exc:
                logger.warning("Groq unexpected response (model %s): %s", model, exc)
                last_error = f"model {model} -> bad response: {exc}"
                last_status = status.HTTP_502_BAD_GATEWAY
                continue

        logger.error("All Groq models failed for user %s. Last error: %s", request.user.id, last_error)
        if last_status == status.HTTP_504_GATEWAY_TIMEOUT:
            return Response(
                {"error": "AI javob berish vaqti tugadi. Qayta urinib ko'ring."},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        return Response(
            {"error": "AI xizmatiga ulanishda xatolik yuz berdi."},
            status=status.HTTP_502_BAD_GATEWAY,
        )