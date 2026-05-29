import requests
from django.conf import settings
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import UserProgress, DailyPlan
from ..serializers.progress import UserProgressSerializer, DailyPlanSerializer
from drf_yasg.utils import swagger_auto_schema

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

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openrouter/auto",
                "messages": [{"role": "user", "content": prompt}]
            }
        )

        response_data = response.json()
        plan_text = response_data['choices'][0]['message']['content']

        plan = DailyPlan.objects.create(
            user=request.user,
            plan_text=plan_text,
            ai_generated=True
        )

        serializer = DailyPlanSerializer(plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)