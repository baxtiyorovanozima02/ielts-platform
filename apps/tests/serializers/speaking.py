from rest_framework import serializers
from ..models import (
    SpeakingResult, ExaminerVoice, SpeakingSession, SpeakingSessionAnswer, Question,
)


class SpeakingResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakingResult
        fields = ('id', 'test', 'session', 'audio_file', 'transcript', 'ai_feedback', 'band_score', 'created_at')
        read_only_fields = ('transcript', 'ai_feedback', 'band_score', 'created_at')


class ExaminerVoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExaminerVoice
        fields = ('id', 'name', 'gender', 'accent', 'preview_audio_url', 'avatar_id')


class SpeakingQuestionSerializer(serializers.ModelSerializer):
    cue_card_points = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = (
            'id', 'text', 'part', 'order',
            'prep_seconds', 'answer_seconds', 'cue_card_points',
        )

    def get_cue_card_points(self, obj):
        if not obj.cue_card_points:
            return []
        return [line.strip() for line in obj.cue_card_points.splitlines() if line.strip()]


class SpeakingSessionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakingSessionAnswer
        fields = ('id', 'question', 'audio_file', 'transcript', 'duration_seconds', 'answered_at')
        read_only_fields = ('answered_at',)


class SpeakingSessionStartSerializer(serializers.Serializer):
    voice_id = serializers.IntegerField(required=False, allow_null=True)


class SpeakingSessionSubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    transcript = serializers.CharField(required=False, allow_blank=True)
    duration_seconds = serializers.IntegerField(required=False, default=0)


class SpeakingSessionSerializer(serializers.ModelSerializer):
    voice = ExaminerVoiceSerializer(read_only=True)
    total_questions = serializers.SerializerMethodField()
    answered_count = serializers.SerializerMethodField()

    class Meta:
        model = SpeakingSession
        fields = (
            'id', 'test', 'voice', 'current_part', 'current_question_order',
            'status', 'started_at', 'finished_at', 'total_questions', 'answered_count',
        )

    def get_total_questions(self, obj):
        return obj.test.questions.filter(part__isnull=False).count()

    def get_answered_count(self, obj):
        return obj.answers.count()


class SpeakingSessionDetailSerializer(SpeakingSessionSerializer):
    answers = SpeakingSessionAnswerSerializer(many=True, read_only=True)

    class Meta(SpeakingSessionSerializer.Meta):
        fields = SpeakingSessionSerializer.Meta.fields + ('answers',)