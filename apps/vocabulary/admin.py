from django.contrib import admin
from .models import Word, WordReview


class WordReviewInline(admin.TabularInline):
    model = WordReview
    extra = 0
    readonly_fields = ('quality', 'next_review', 'interval', 'repetitions', 'ease_factor', 'reviewed_at')
    can_delete = False


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ('word', 'translation', 'topic', 'user', 'created_at')
    list_filter = ('topic',)
    search_fields = ('word', 'translation', 'user__username')
    inlines = [WordReviewInline]


@admin.register(WordReview)
class WordReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'word', 'quality', 'next_review', 'interval', 'repetitions')
    list_filter = ('quality',)
    search_fields = ('user__username', 'word__word')
    readonly_fields = ('reviewed_at',)