import json
import re
import requests
from django.conf import settings
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import UserProgress, DailyPlan
from ..serializers.progress import UserProgressSerializer, DailyPlanSerializer
from drf_yasg.utils import swagger_auto_schema


def extract_json(raw: str) -> dict:
    """
    AI javobidan JSON ni ishonchli ajratib oladi.
    """
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
    if match:
        return json.loads(match.group(1).strip())

    match = re.search(r'\{[\s\S]*\}', raw)
    if match:
        return json.loads(match.group(0).strip())

    raise ValueError("JSON topilmadi")

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]


def call_gemini(prompt, timeout=110):
    """
    Groq API ga so'rov yuboradi. Bir nechta model bilan, biri ishlamasa
    keyingisi sinab ko'riladi.
    """
    last_error = None

    for model in GROQ_MODELS:
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4000,
                    "temperature": 0.7,
                },
                timeout=timeout,
            )

            if response.status_code != 200:
                last_error = f"{model}: status {response.status_code} - {response.text[:200]}"
                continue

            data = response.json()

            try:
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                last_error = f"{model}: javob strukturasi noto'g'ri - {str(data)[:200]}"
                continue

            if not content or not content.strip():
                last_error = f"{model}: bo'sh javob qaytdi"
                continue

            return content

        except Exception as e:
            last_error = f"{model}: {str(e)}"
            continue

    raise Exception(f"Barcha modellar ishlamadi. Oxirgi xato: {last_error}")


class UserProgressView(generics.ListAPIView):
    serializer_class = UserProgressSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Foydalanuvchi progressi")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return UserProgress.objects.filter(
            user=self.request.user
        ).select_related('section')


class DailyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Kunlik o'quv reja")
    def get(self, request):
        from datetime import date
        today = date.today()
        plan = DailyPlan.objects.filter(user=request.user, date=today).first()
        if plan:
            serializer = DailyPlanSerializer(plan)
            return Response(serializer.data)

        progress = UserProgress.objects.filter(user=request.user).select_related('section')

        if not progress.exists():
            return Response({'message': 'Hali hech qanday test topshirilmagan.'}, status=status.HTTP_200_OK)

        progress_text = "\n".join([
            f"{p.section.name}: average band score {p.average_band_score}, total tests {p.total_tests_taken}"
            for p in progress
        ])

        prompt = f"""
        You are an IELTS coach. Based on the student's progress below, create a personalized daily study plan for today.

        Student Progress:
        {progress_text}

        Create a specific, actionable daily plan with time allocations for each skill.
        Focus more on weaker areas. Keep it concise and motivating.
        """

        try:
            plan_text = call_gemini(prompt)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        plan = DailyPlan.objects.create(
            user=request.user,
            plan_text=plan_text,
            ai_generated=True
        )

        serializer = DailyPlanSerializer(plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AIGeneratePlanView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="AI yordamida shaxsiy o'quv reja generatsiyasi")
    def post(self, request):
        duration = request.data.get('duration', '1day')
        skill = request.data.get('skill', 'all')

        duration_label = {'1day': '1 kunlik', '1week': '1 haftalik', '1month': '1 oylik'}.get(duration, '1 kunlik')
        skill_text = (
            "barcha ko'nikmalar: Reading, Listening, Writing, Speaking, Vocabulary"
            if skill == 'all' else skill
        )
        task_count = {
            '1day': '5-6 ta vazifa.',
            '1week': '18-22 ta vazifa, turli kunlarga taqsimlangan.',
            '1month': '28-35 ta vazifa, haftalik guruhlar bilan.',
        }.get(duration, '5-6 ta vazifa.')

        prompt = f"""Siz professional IELTS o'qituvchisiz. {duration_label} o'quv rejasini tuzing.
Ko'nikma yo'nalishi: {skill_text}

FAQAT JSON formatida javob bering. Boshqa hech narsa yozmang:
{{
  "title": "Reja sarlavhasi (qisqa, motivatsion, o'zbekcha)",
  "summary": "Reja haqida 1-2 jumla (o'zbekcha)",
  "targetBand": "Maqsad band score (masalan: Band 6.5+)",
  "motivation": "Motivatsion qisqa xabar (o'zbekcha)",
  "tasks": [
    {{
      "type": "Reading|Listening|Writing|Speaking|Vocabulary|Grammar",
      "title": "Aniq vazifa tavsifi (o'zbekcha)",
      "duration": "Vaqt (masalan: 30 daqiqa)",
      "tip": "Foydali maslahat (o'zbekcha, 1 jumla)"
    }}
  ]
}}

{task_count}
Faqat JSON, boshqa matn yoq."""

        try:
            raw = call_gemini(prompt, timeout=110)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        try:
            result = extract_json(raw)
        except Exception:
            return Response(
                {'error': "AI javobini o'qib bo'lmadi", 'raw': raw[:500]},
                status=status.HTTP_502_BAD_GATEWAY
            )

        required = ['title', 'summary', 'targetBand', 'motivation', 'tasks']
        missing = [f for f in required if f not in result]
        if missing:
            return Response(
                {'error': f"AI javobida maydonlar yetishmayapti: {missing}", 'raw': raw[:500]},
                status=status.HTTP_502_BAD_GATEWAY
            )

        if not isinstance(result.get('tasks'), list) or len(result['tasks']) == 0:
            return Response(
                {'error': "AI tasks ro'yxatini qaytarmadi", 'raw': raw[:500]},
                status=status.HTTP_502_BAD_GATEWAY
            )

        return Response(result, status=status.HTTP_200_OK)