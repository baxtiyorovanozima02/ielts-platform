from django.contrib import admin
from django.utils.html import format_html
from .models import Section, Test, Question, Answer, UserTestResult, SpeakingResult, UserProgress, DailyPlan


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    fields = ('text', 'is_correct')


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    fields = ('order', 'question_type', 'text')
    ordering = ('order',)
    show_change_link = True


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'test_count')

    def test_count(self, obj):
        return obj.tests.count()
    test_count.short_description = "Testlar soni"


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'duration_minutes', 'question_count', 'is_active', 'created_at')
    list_filter = ('section', 'is_active')
    search_fields = ('title',)
    list_editable = ('is_active',)
    inlines = [QuestionInline]

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = "Savollar"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'test', 'question_type', 'order', 'answer_count')
    list_filter = ('question_type', 'test__section')
    search_fields = ('text', 'test__title')
    ordering = ('test', 'order')
    inlines = [AnswerInline]

    def short_text(self, obj):
        return obj.text[:80] + '...' if len(obj.text) > 80 else obj.text
    short_text.short_description = "Savol"

    def answer_count(self, obj):
        return obj.answers.count()
    answer_count.short_description = "Javoblar"


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('text',)


@admin.register(UserTestResult)
class UserTestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'band_score', 'created_at')
    list_filter = ('test__section',)
    search_fields = ('user__username', 'test__title')
    readonly_fields = ('user', 'test', 'essay_text', 'ai_feedback', 'band_score', 'created_at')


@admin.register(SpeakingResult)
class SpeakingResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'band_score', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('user', 'test', 'transcript', 'ai_feedback', 'band_score', 'created_at')


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'section', 'average_band_score', 'total_tests_taken', 'last_updated')
    list_filter = ('section',)
    search_fields = ('user__username',)
    readonly_fields = ('user', 'section', 'average_band_score', 'total_tests_taken', 'last_updated')


@admin.register(DailyPlan)
class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'ai_generated', 'created_at')
    list_filter = ('ai_generated',)
    search_fields = ('user__username',)
    readonly_fields = ('user', 'date', 'plan_text', 'created_at')