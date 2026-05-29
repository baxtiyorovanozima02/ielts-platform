from rest_framework import generics, permissions
from ..models import Section, Test, Question
from ..serializers.section import SectionSerializer
from ..serializers.test import TestSerializer, QuestionSerializer
from drf_yasg.utils import swagger_auto_schema

class SectionListView(generics.ListAPIView):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="Bo'limlar ro'yxati")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TestListView(generics.ListAPIView):
    serializer_class = TestSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="Testlar ro'yxati")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        section = self.request.query_params.get('section')
        if section:
            return Test.objects.filter(section__name=section, is_active=True)
        return Test.objects.filter(is_active=True)


class TestDetailView(generics.RetrieveAPIView):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="Test tafsiloti")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class QuestionListView(generics.ListAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="Savollar ro'yxati")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        test_id = self.kwargs.get('test_id')
        return Question.objects.filter(test_id=test_id)