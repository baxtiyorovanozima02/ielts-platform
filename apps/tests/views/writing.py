import requests
from django.conf import settings
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Test, UserTestResult
from ..serializers.writing import UserTestResultSerializer


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

        prompt = f"""
        You are an IELTS examiner. Evaluate the following essay and provide:
        1. Band score (0-9)
        2. Task Achievement feedback
        3. Coherence and Cohesion feedback
        4. Lexical Resource feedback
        5. Grammatical Range feedback

        Essay: {essay_text}

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

        result = UserTestResult.objects.create(
            user=request.user,
            test=test,
            essay_text=essay_text,
            ai_feedback=ai_feedback,
            band_score=band_score
        )

        return Response({
            'id': result.id,
            'band_score': result.band_score,
            'ai_feedback': result.ai_feedback,
        }, status=status.HTTP_201_CREATED)


class WritingResultListView(generics.ListAPIView):
    serializer_class = UserTestResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserTestResult.objects.filter(
            user=self.request.user
        ).select_related('test').order_by('-created_at')