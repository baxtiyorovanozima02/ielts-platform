from django.urls import path
from .views import (
    SectionListView,
    TestListView,
    TestDetailView,
    QuestionListView,
    WritingEvaluationView,
    WritingResultListView,
    SpeakingEvaluationView,
    SpeakingResultListView,
    UserProgressView,
    DailyPlanView,
)

urlpatterns = [
    path('sections/', SectionListView.as_view(), name='section-list'),
    path('tests/', TestListView.as_view(), name='test-list'),
    path('tests/<int:pk>/', TestDetailView.as_view(), name='test-detail'),
    path('tests/<int:test_id>/questions/', QuestionListView.as_view(), name='question-list'),
    path('tests/<int:test_id>/evaluate/', WritingEvaluationView.as_view(), name='writing-evaluate'),
    path('results/writing/', WritingResultListView.as_view(), name='writing-results'),
    path('tests/<int:test_id>/speaking/', SpeakingEvaluationView.as_view(), name='speaking-evaluate'),
    path('results/speaking/', SpeakingResultListView.as_view(), name='speaking-results'),
    path('progress/', UserProgressView.as_view(), name='user-progress'),
    path('daily-plan/', DailyPlanView.as_view(), name='daily-plan'),
]