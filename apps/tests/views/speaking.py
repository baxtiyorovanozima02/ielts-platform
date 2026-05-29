from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Test, SpeakingResult
from ..serializers.speaking import SpeakingResultSerializer
from ..tasks import evaluate_speaking_task
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class SpeakingEvaluationView(APIView):
    permission_classes = [IsAuthenticated]


    @swagger_auto_schema(
        operation_summary="Speaking baholash",
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