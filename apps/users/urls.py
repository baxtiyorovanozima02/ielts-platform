from django.urls import path
from .views import MeView, UpdateXPView, UpdateDailyGoalView

urlpatterns = [
    path('me/', MeView.as_view(), name='user-me'),
    path('xp/', UpdateXPView.as_view(), name='user-xp'),
    path('daily-goal/', UpdateDailyGoalView.as_view(), name='user-daily-goal'),
]