from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Test, UserTestResult
from ..serializers.writing import UserTestResultSerializer
from ..tasks import evaluate_writing_task


class WritingEvaluationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, test_id):
        essay_text = request.data.get('essay_text')
        if not essay_text:
            return Response({'error': 'essay_text required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return Response({'error': 'Test not found'}, status=status.HTTP_404_NOT_FOUND)

        result = UserTestResult.objects.create(
            user=request.user,
            test=test,
            essay_text=essay_text,
        )

        evaluate_writing_task.delay(result.id)

        return Response({
            'id': result.id,
            'message': 'Evaluation started. Check results shortly.',
        }, status=status.HTTP_202_ACCEPTED)


class WritingResultListView(generics.ListAPIView):
    serializer_class = UserTestResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserTestResult.objects.filter(
            user=self.request.user
        ).select_related('test').order_by('-created_at')