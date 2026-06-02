from rest_framework import serializers
from .models import SubscriptionPlan, Subscription, Payment


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'plan_type', 'price', 'duration_days', 'description']


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'status', 'started_at', 'expires_at', 'is_active']


class PaymentSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'plan', 'amount', 'payment_method',
            'transaction_id', 'screenshot', 'status', 'note',
            'created_at', 'confirmed_at'
        ]


class PaymentCreateSerializer(serializers.Serializer):
    plan = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.filter(is_active=True)
    )
    payment_method = serializers.ChoiceField(
        choices=['payme', 'click', 'transfer']
    )
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    screenshot = serializers.ImageField(required=False)