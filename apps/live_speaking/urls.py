from django.urls import path

from .views import (
    LiveSpeakingSessionStartView,
    LiveSpeakingSessionDetailView,
    LiveSpeakingSessionEndView,
    LiveSpeakingSessionListView,
)

app_name = 'live_speaking'

urlpatterns = [
    path('sessions/', LiveSpeakingSessionListView.as_view(), name='session-list'),
    path('sessions/start/', LiveSpeakingSessionStartView.as_view(), name='session-start'),
    path('sessions/<int:session_id>/', LiveSpeakingSessionDetailView.as_view(), name='session-detail'),
    path('sessions/<int:session_id>/end/', LiveSpeakingSessionEndView.as_view(), name='session-end'),
]