from rest_framework import serializers
from .models import Section, Test, Question, Answer, UserTestResult

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ('id', 'text', 'is_correct')

class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ('id', 'text', 'question_type', 'order', 'answers')

class TestSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Test
        fields = ('id', 'title', 'section', 'duration_minutes', 'is_active', 'created_at', 'questions')

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ('id', 'name', 'description')


class UserTestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTestResult
        fields = ('id', 'test', 'essay_text', 'ai_feedback', 'band_score', 'created_at')
        read_only_fields = ('ai_feedback', 'band_score', 'created_at')