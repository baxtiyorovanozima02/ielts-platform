from rest_framework import generics, permissions
from .models import SubscriptionPlan, Subscription
from .serializers import SubscriptionPlanSerializer, SubscriptionSerializer


class SubscriptionPlanListView(generics.ListAPIView):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class UserSubscriptionView(generics.RetrieveAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return Subscription.objects.filter(
            user=self.request.user,
            is_active=True
        ).first()