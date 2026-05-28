import requests
from django.conf import settings
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Test, SpeakingResult
from ..serializers.speaking import SpeakingResultSerializer


class SpeakingEvaluationView(APIView):
    permission_classes = [IsAuthenticated]

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
            transcript = "Audio transcript placeholder - real transcription service needed"

        prompt = f"""
        You are an IELTS examiner. Evaluate the following speaking transcript and provide:
        1. Band score (0-9)
        2. Fluency and Coherence feedback
        3. Lexical Resource feedback
        4. Grammatical Range and Accuracy feedback
        5. Pronunciation feedback

        Transcript: {transcript}

        Respond in this format:
        Band Score: X
        Feedback: ...
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
        ai_feedback = response_data['choices'][0]['message']['content']

        band_line = ai_feedback.split('\n')[0]
        try:
            band_score = float(band_line.split(':')[1].strip())
        except Exception:
            band_score = None

        result = SpeakingResult.objects.create(
            user=request.user,
            test=test,
            audio_file=audio_file,
            transcript=transcript,
            ai_feedback=ai_feedback,
            band_score=band_score
        )

        return Response({
            'id': result.id,
            'transcript': result.transcript,
            'band_score': result.band_score,
            'ai_feedback': result.ai_feedback,
        }, status=status.HTTP_201_CREATED)


class SpeakingResultListView(generics.ListAPIView):
    serializer_class = SpeakingResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SpeakingResult.objects.filter(
            user=self.request.user
        ).select_related('test').order_by('-created_at')