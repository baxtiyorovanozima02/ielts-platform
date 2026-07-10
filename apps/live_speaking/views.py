from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import LiveSpeakingSession
from .serializers import LiveSpeakingSessionSerializer, LiveSpeakingSessionDetailSerializer
from .avatar_service import create_avatar_session_token, get_avatar_id_for_voice, AvatarServiceError
from apps.tests.models import Test, ExaminerVoice


class LiveSpeakingSessionStartView(APIView):
    """AI avatar bilan jonli suhbat sessiyasini boshlaydi.

    Bu view sessiya yozuvini yaratadi VA HeyGen avatar tokenini ham qaytaradi,
    shunda frontend bir so'rov bilan: (1) WebSocket manzilini, (2) avatar
    ko'rsatish uchun kerakli tokenni oladi.
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

        try:
            avatar_token = create_avatar_session_token()
        except AvatarServiceError as exc:
            avatar_token = None

        return Response({
            'session': LiveSpeakingSessionSerializer(session).data,
            'websocket_url': f"/ws/live-speaking/{session.id}/",
            'avatar_token': avatar_token,
            'avatar_id': get_avatar_id_for_voice(voice),
        }, status=status.HTTP_201_CREATED)


class LiveSpeakingAvatarTokenView(APIView):
    """Mavjud sessiya uchun avatar tokenini qaytadan olish kerak bo'lganda
    (masalan, token muddati tugagan yoki sahifa qayta yuklangan bo'lsa)."""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Avatar tokenini qayta olish")
    def get(self, request, session_id):
        session = LiveSpeakingSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return Response({'error': 'Sessiya topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        try:
            avatar_token = create_avatar_session_token()
        except AvatarServiceError:
            return Response({'error': 'Avatar xizmatiga ulanib bo\'lmadi'}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({
            'avatar_token': avatar_token,
            'avatar_id': get_avatar_id_for_voice(session.voice),
        })


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