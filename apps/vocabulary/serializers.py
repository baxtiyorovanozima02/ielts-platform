from rest_framework import serializers
from .models import Word, WordReview


class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ('id', 'word', 'translation', 'example', 'created_at')
        read_only_fields = ('created_at',)


class WordReviewSerializer(serializers.ModelSerializer):
    word_text = serializers.CharField(source='word.word', read_only=True)
    translation = serializers.CharField(source='word.translation', read_only=True)

    class Meta:
        model = WordReview
        fields = ('id', 'word', 'word_text', 'translation', 'quality', 'next_review', 'interval', 'repetitions', 'ease_factor', 'reviewed_at')
        read_only_fields = ('next_review', 'interval', 'repetitions', 'ease_factor', 'reviewed_at')