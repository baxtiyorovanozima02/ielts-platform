from django.contrib import admin
from .models import Section, Test, Question, Answer

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'duration_minutes', 'is_active', 'created_at')
    list_filter = ('section', 'is_active')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'question_type', 'order')
    list_filter = ('question_type',)

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct',)