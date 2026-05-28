from rest_framework import serializers
from ..models import UserProgress, DailyPlan


class UserProgressSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source='section.name', read_only=True)

    class Meta:
        model = UserProgress
        fields = ('id', 'section', 'section_name', 'average_band_score', 'total_tests_taken', 'last_updated')
        read_only_fields = ('average_band_score', 'total_tests_taken', 'last_updated')


class DailyPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyPlan
        fields = ('id', 'date', 'plan_text', 'ai_generated', 'created_at')
        read_only_fields = ('plan_text', 'ai_generated', 'date', 'created_at')