from rest_framework import serializers
from ..models import UserTestResult


class UserTestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTestResult
        fields = ('id', 'test', 'essay_text', 'ai_feedback', 'band_score', 'created_at')
        read_only_fields = ('ai_feedback', 'band_score', 'created_at')