from django.urls import path
from .views import SubscriptionPlanListView, UserSubscriptionView

urlpatterns = [
    path('plans/', SubscriptionPlanListView.as_view(), name='subscription-plans'),
    path('my-subscription/', UserSubscriptionView.as_view(), name='my-subscription'),
]