from django.urls import path
from .views import SectionListView, TestListView, TestDetailView, QuestionListView

urlpatterns = [
    path('sections/', SectionListView.as_view(), name='section-list'),
    path('tests/', TestListView.as_view(), name='test-list'),
    path('tests/<int:pk>/', TestDetailView.as_view(), name='test-detail'),
    path('tests/<int:test_id>/questions/', QuestionListView.as_view(), name='question-list'),
]