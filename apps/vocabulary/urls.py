from django.urls import path
from .views import WordListCreateView, WordDetailView, DueWordsView, WordReviewView

urlpatterns = [
    path('words/', WordListCreateView.as_view(), name='word-list'),
    path('words/<int:pk>/', WordDetailView.as_view(), name='word-detail'),
    path('words/due/', DueWordsView.as_view(), name='due-words'),
    path('words/review/', WordReviewView.as_view(), name='word-review'),
]