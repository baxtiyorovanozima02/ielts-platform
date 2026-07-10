from rest_framework import serializers

from .models import LiveSpeakingSession, LiveSpeakingMessage
from apps.tests.serializers.speaking import ExaminerVoiceSerializer


class LiveSpeakingMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveSpeakingMessage
        fields = ['id', 'role', 'text', 'created_at']


class LiveSpeakingSessionSerializer(serializers.ModelSerializer):
    voice = ExaminerVoiceSerializer(read_only=True)

    class Meta:
        model = LiveSpeakingSession
        fields = ['id', 'test', 'voice', 'status', 'started_at', 'ended_at']


class LiveSpeakingSessionDetailSerializer(serializers.ModelSerializer):
    voice = ExaminerVoiceSerializer(read_only=True)
    messages = LiveSpeakingMessageSerializer(many=True, read_only=True)

    class Meta:
        model = LiveSpeakingSession
        fields = ['id', 'test', 'voice', 'status', 'started_at', 'ended_at', 'messages']