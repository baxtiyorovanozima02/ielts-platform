from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
from .models import User


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'username', 'email', 'password', 'phone_number')


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = User
        ref_name = 'CustomUser'
        fields = (
            'id', 'username', 'email', 'phone_number', 'is_premium', 'created_at',
            'streak_count', 'last_visit_date', 'xp_total', 'daily_goal_done', 'daily_goal_date',
        )