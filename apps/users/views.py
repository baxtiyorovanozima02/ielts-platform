from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from .serializers import UserSerializer
from drf_yasg.utils import swagger_auto_schema


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Mening profilim")
    def get(self, request):
        user = request.user
        today = date.today()
        yesterday = today - timedelta(days=1)

        if user.last_visit_date == today:
            pass
        elif user.last_visit_date == yesterday:
            user.streak_count += 1
            user.last_visit_date = today
            user.save(update_fields=['streak_count', 'last_visit_date'])
        else:
            user.streak_count = 1
            user.last_visit_date = today
            user.save(update_fields=['streak_count', 'last_visit_date'])

        serializer = UserSerializer(user)
        return Response(serializer.data)


class UpdateXPView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="XP qo'shish")
    def post(self, request):
        amount = request.data.get('amount', 0)
        if not isinstance(amount, int) or amount <= 0:
            return Response({'error': 'amount musbat son bo\'lishi kerak'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.xp_total += amount
        user.save(update_fields=['xp_total'])
        return Response({'xp_total': user.xp_total})


class UpdateDailyGoalView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Kunlik maqsadni yangilash")
    def post(self, request):
        user = request.user
        today = date.today()

        if user.daily_goal_date != today:
            user.daily_goal_done = 0
            user.daily_goal_date = today

        user.daily_goal_done += 1
        user.save(update_fields=['daily_goal_done', 'daily_goal_date'])
        return Response({'daily_goal_done': user.daily_goal_done, 'daily_goal_date': str(today)})