from django.contrib import admin
from .models import Word, WordReview


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'word', 'translation', 'created_at')


@admin.register(WordReview)
class WordReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'word', 'quality', 'next_review', 'interval')