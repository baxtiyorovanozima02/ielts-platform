from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..serializers.speaking import (
    SpeakingResultSerializer,
    ExaminerVoiceSerializer,
    SpeakingQuestionSerializer,
    SpeakingSessionSerializer,
    SpeakingSessionDetailSerializer,
)
from ..tasks import evaluate_speaking_task, evaluate_speaking_session_task
from ..models import Test, SpeakingResult, UserProgress, ExaminerVoice, SpeakingSession, SpeakingSessionAnswer, Question
from apps.live_speaking.avatar_service import (
    create_avatar_session_token,
    get_avatar_id_for_voice,
    AvatarServiceError,
)


def _ordered_speaking_questions(test):
    """Part 1 -> Part 2 -> Part 3 tartibida, har bir part ichida order bo'yicha saralangan savollar."""
    return list(test.questions.filter(part__isnull=False).order_by('part', 'order'))


class ExaminerVoiceListView(generics.ListAPIView):
    """Foydalanuvchi mock imtihonni boshlashdan oldin examiner ovozini tanlashi uchun ro'yxat."""
    serializer_class = ExaminerVoiceSerializer
    permission_classes = [IsAuthenticated]
    queryset = ExaminerVoice.objects.filter(is_active=True)

    @swagger_auto_schema(operation_summary="Examiner ovozlari ro'yxati")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SpeakingSessionStartView(APIView):
    """Yangi mock speaking sessiya boshlaydi va Part 1 dagi birinchi savolni qaytaradi."""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Speaking mock sessiyani boshlash",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'voice_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ExaminerVoice id (ixtiyoriy)"),
            }
        )
    )
    def post(self, request, test_id):
        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        questions = _ordered_speaking_questions(test)
        if not questions:
            return Response(
                {'error': 'Bu testda speaking savollari (part 1/2/3) sozlanmagan'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        voice = None
        voice_id = request.data.get('voice_id')
        if voice_id:
            voice = ExaminerVoice.objects.filter(id=voice_id, is_active=True).first()
            if not voice:
                return Response({'error': 'Tanlangan ovoz topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        session = SpeakingSession.objects.create(
            user=request.user,
            test=test,
            voice=voice,
            current_part=questions[0].part,
            current_question_order=0,
            status='in_progress',
        )

        try:
            avatar_token = create_avatar_session_token()
        except AvatarServiceError:
            avatar_token = None

        first_question = questions[0]
        return Response({
            'session': SpeakingSessionSerializer(session).data,
            'question': SpeakingQuestionSerializer(first_question).data,
            'avatar_token': avatar_token,
            'avatar_id': get_avatar_id_for_voice(voice),
        }, status=status.HTTP_201_CREATED)


class SpeakingSessionAvatarTokenView(APIView):
    """Mock sessiya davomida HeyGen tokeni muddati tugasa, frontend shu orqali
    yangi token so'rab oladi (masalan, Part 2 dan Part 3 ga o'tayotganda)."""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Mock speaking sessiyasi uchun avatar tokenini qayta olish")
    def get(self, request, session_id):
        session = SpeakingSession.objects.filter(id=session_id, user=request.user).first()
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


class SpeakingSessionCurrentQuestionView(APIView):
    """Sessiyaning hozirgi holatiga mos savolni qaytaradi (masalan, sahifa qayta yuklanganda)."""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Sessiyaning joriy savoli")
    def get(self, request, session_id):
        session = SpeakingSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return Response({'error': 'Sessiya topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        questions = _ordered_speaking_questions(session.test)

        if session.status != 'in_progress' or session.current_question_order >= len(questions):
            return Response({
                'session': SpeakingSessionSerializer(session).data,
                'question': None,
                'finished': True,
            })

        question = questions[session.current_question_order]
        return Response({
            'session': SpeakingSessionSerializer(session).data,
            'question': SpeakingQuestionSerializer(question).data,
            'finished': False,
        })


class SpeakingSessionAnswerView(APIView):
    """Joriy savolga javob (audio va/yoki transkript) qabul qiladi va keyingi savolga o'tkazadi."""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Sessiya savoliga javob yuborish",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['question_id'],
            properties={
                'question_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'transcript': openapi.Schema(type=openapi.TYPE_STRING),
                'duration_seconds': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )
    )
    def post(self, request, session_id):
        session = SpeakingSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return Response({'error': 'Sessiya topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if session.status != 'in_progress':
            return Response({'error': 'Bu sessiya allaqachon yakunlangan'}, status=status.HTTP_400_BAD_REQUEST)

        questions = _ordered_speaking_questions(session.test)
        if session.current_question_order >= len(questions):
            return Response({'error': 'Sessiyada javob kutilayotgan savol qolmagan'}, status=status.HTTP_400_BAD_REQUEST)

        expected_question = questions[session.current_question_order]

        question_id = request.data.get('question_id')
        if not question_id or int(question_id) != expected_question.id:
            return Response(
                {'error': 'question_id joriy kutilayotgan savolga mos kelmadi', 'expected_question_id': expected_question.id},
                status=status.HTTP_400_BAD_REQUEST,
            )

        transcript = request.data.get('transcript', '')
        audio_file = request.FILES.get('audio_file')
        duration_seconds = int(request.data.get('duration_seconds') or 0)

        if not transcript and not audio_file:
            return Response({'error': 'transcript yoki audio_file kerak'}, status=status.HTTP_400_BAD_REQUEST)

        SpeakingSessionAnswer.objects.create(
            session=session,
            question=expected_question,
            audio_file=audio_file,
            transcript=transcript or '',
            duration_seconds=duration_seconds,
        )

        next_index = session.current_question_order + 1

        if next_index >= len(questions):
            session.status = 'completed'
            session.finished_at = timezone.now()
            session.current_question_order = next_index
            session.save(update_fields=['status', 'finished_at', 'current_question_order'])

            evaluate_speaking_session_task.delay(session.id)

            progress, _ = UserProgress.objects.get_or_create(user=request.user, section=session.test.section)
            progress.total_tests_taken += 1
            progress.save(update_fields=['total_tests_taken'])

            return Response({
                'finished': True,
                'session': SpeakingSessionSerializer(session).data,
                'message': "Barcha qismlar yakunlandi. Natija tez orada tayyor bo'ladi.",
            }, status=status.HTTP_200_OK)

        next_question = questions[next_index]
        session.current_question_order = next_index
        session.current_part = next_question.part
        session.save(update_fields=['current_question_order', 'current_part'])

        return Response({
            'finished': False,
            'session': SpeakingSessionSerializer(session).data,
            'question': SpeakingQuestionSerializer(next_question).data,
        }, status=status.HTTP_200_OK)


class SpeakingSessionAbandonView(APIView):
    """Foydalanuvchi sessiyani muddatidan oldin tashlab ketsa, holatni belgilash uchun."""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Sessiyani bekor qilish")
    def post(self, request, session_id):
        session = SpeakingSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return Response({'error': 'Sessiya topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if session.status == 'in_progress':
            session.status = 'abandoned'
            session.finished_at = timezone.now()
            session.save(update_fields=['status', 'finished_at'])

        return Response(SpeakingSessionSerializer(session).data)


class SpeakingSessionResultView(APIView):
    """Yakunlangan sessiya bo'yicha AI baholash natijasini olish (tayyor bo'lmasa hali kutilmoqda deb qaytaradi)."""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Sessiya natijasi")
    def get(self, request, session_id):
        session = SpeakingSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return Response({'error': 'Sessiya topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        result = session.results.order_by('-created_at').first()
        if not result:
            return Response({'ready': False, 'session': SpeakingSessionSerializer(session).data})

        return Response({
            'ready': result.band_score is not None,
            'session': SpeakingSessionSerializer(session).data,
            'result': SpeakingResultSerializer(result).data,
        })



class SpeakingEvaluationView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Speaking baholash (eski, oddiy usul)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'transcript': openapi.Schema(type=openapi.TYPE_STRING),
            }
        )
    )
    def post(self, request, test_id):
        transcript = request.data.get('transcript')
        audio_file = request.FILES.get('audio_file')

        if not transcript and not audio_file:
            return Response(
                {'error': 'transcript yoki audio_file kerak'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if not transcript:
            transcript = "Audio transcript placeholder"

        result = SpeakingResult.objects.create(
            user=request.user,
            test=test,
            audio_file=audio_file,
            transcript=transcript,
        )

        evaluate_speaking_task.delay(result.id)

        section = test.section
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            section=section,
        )
        progress.total_tests_taken += 1
        progress.save(update_fields=['total_tests_taken'])

        return Response({
            'id': result.id,
            'message': 'Evaluation started. Check results shortly.',
        }, status=status.HTTP_202_ACCEPTED)


class SpeakingResultListView(generics.ListAPIView):
    serializer_class = SpeakingResultSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Speaking natijalari")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return SpeakingResult.objects.filter(
            user=self.request.user
        ).select_related('test').order_by('-created_at')