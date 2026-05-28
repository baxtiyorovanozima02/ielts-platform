from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Test, SpeakingResult
from ..serializers.speaking import SpeakingResultSerializer
from ..tasks import evaluate_speaking_task


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
            transcript = "Audio transcript placeholder"

        result = SpeakingResult.objects.create(
            user=request.user,
            test=test,
            audio_file=audio_file,
            transcript=transcript,
        )

        evaluate_speaking_task.delay(result.id)

        return Response({
            'id': result.id,
            'message': 'Evaluation started. Check results shortly.',
        }, status=status.HTTP_202_ACCEPTED)


class SpeakingResultListView(generics.ListAPIView):
    serializer_class = SpeakingResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SpeakingResult.objects.filter(
            user=self.request.user
        ).select_related('test').order_by('-created_at')