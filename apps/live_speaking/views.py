from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import LiveSpeakingSession
from .serializers import LiveSpeakingSessionSerializer, LiveSpeakingSessionDetailSerializer
from apps.tests.models import Test, ExaminerVoice


class LiveSpeakingSessionStartView(APIView):
    """AI avatar bilan jonli suhbat sessiyasini boshlaydi.

    Bu view faqat sessiya yozuvini yaratadi (DB'da). Haqiqiy audio oqimi
    keyingi qadamda qo'shiladigan WebSocket consumer orqali boradi:
    ws/live-speaking/<session_id>/
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Live speaking sessiyasini boshlash",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'test_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Ixtiyoriy: mavzu sifatida ulanadigan test"),
                'voice_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Tanlangan AI ovoz/avatar"),
            }
        ),
        responses={201: LiveSpeakingSessionSerializer()},
    )
    def post(self, request):
        test = None
        test_id = request.data.get('test_id')
        if test_id:
            test = Test.objects.filter(id=test_id).first()
            if not test:
                return Response({'error': 'Test topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        voice = None
        voice_id = request.data.get('voice_id')
        if voice_id:
            voice = ExaminerVoice.objects.filter(id=voice_id, is_active=True).first()
            if not voice:
                return Response({'error': 'Tanlangan ovoz/avatar topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        session = LiveSpeakingSession.objects.create(
            user=request.user,
            test=test,
            voice=voice,
            status='connecting',
        )

        return Response({
            'session': LiveSpeakingSessionSerializer(session).data,
            'websocket_url': f"/ws/live-speaking/{session.id}/",
        }, status=status.HTTP_201_CREATED)


class LiveSpeakingSessionDetailView(APIView):
    """Sessiya haqida to'liq ma'lumot: holati va barcha xabarlar tarixi."""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Live speaking sessiya tafsilotlari")
    def get(self, request, session_id):
        session = LiveSpeakingSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return Response({'error': 'Sessiya topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        return Response(LiveSpeakingSessionDetailSerializer(session).data)


class LiveSpeakingSessionEndView(APIView):
    """Foydalanuvchi suhbatni tugatganda sessiyani yopadi."""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Live speaking sessiyasini tugatish")
    def post(self, request, session_id):
        session = LiveSpeakingSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return Response({'error': 'Sessiya topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if session.status != 'ended':
            session.status = 'ended'
            session.ended_at = timezone.now()
            session.save(update_fields=['status', 'ended_at'])

        return Response(LiveSpeakingSessionSerializer(session).data)


class LiveSpeakingSessionListView(generics.ListAPIView):
    """Foydalanuvchining barcha live speaking sessiyalari tarixi."""
    serializer_class = LiveSpeakingSessionSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Live speaking sessiyalari tarixi")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return LiveSpeakingSession.objects.filter(user=self.request.user)