import requests
from django.conf import settings
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Section, Test, Question, UserTestResult
from .serializers import SectionSerializer, TestSerializer, QuestionSerializer



class SectionListView(generics.ListAPIView):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated]

class TestListView(generics.ListAPIView):
    serializer_class = TestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        section = self.request.query_params.get('section')
        if section:
            return Test.objects.filter(section__name=section, is_active=True)
        return Test.objects.filter(is_active=True)

class TestDetailView(generics.RetrieveAPIView):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    permission_classes = [permissions.IsAuthenticated]

class QuestionListView(generics.ListAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        test_id = self.kwargs.get('test_id')
        return Question.objects.filter(test_id=test_id)


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
        print(response_data)
        ai_feedback = response_data['choices'][0]['message']['content']

        band_line = ai_feedback.split('\n')[0]
        try:
            band_score = float(band_line.split(':')[1].strip())
        except:
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
