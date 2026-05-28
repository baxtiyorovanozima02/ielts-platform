from rest_framework import serializers
from ..models import SpeakingResult


class SpeakingResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakingResult
        fields = ('id', 'test', 'audio_file', 'transcript', 'ai_feedback', 'band_score', 'created_at')
        read_only_fields = ('transcript', 'ai_feedback', 'band_score', 'created_at')