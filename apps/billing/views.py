from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import SubscriptionPlan, Subscription, Payment
from .serializers import (
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
)
from .tasks import notify_payment_received, notify_payment_confirmed, notify_payment_rejected


class SubscriptionPlanListView(generics.ListAPIView):
    """Barcha aktiv planlar ro'yxati"""
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class UserSubscriptionView(generics.RetrieveAPIView):
    """Foydalanuvchining aktiv obunasi"""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return Subscription.objects.filter(
            user=self.request.user,
            is_active=True
        ).first()


class PaymentCreateView(APIView):
    """Foydalanuvchi to'lov qilish"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            plan = serializer.validated_data['plan']
            payment = Payment.objects.create(
                user=request.user,
                plan=plan,
                amount=plan.price,
                payment_method=serializer.validated_data['payment_method'],
                transaction_id=serializer.validated_data.get('transaction_id', ''),
                screenshot=serializer.validated_data.get('screenshot'),
            )
            # Email + Telegram xabar yuborish
            notify_payment_received.delay(payment.id)

            return Response({
                'message': "To'lovingiz qabul qilindi! Tez orada tasdiqlanadi.",
                'payment_id': payment.id,
                'status': payment.status,
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentListView(generics.ListAPIView):
    """Foydalanuvchining barcha to'lovlari"""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by('-created_at')


class AdminPaymentConfirmView(APIView):
    """Admin to'lovni tasdiqlaydi"""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id, status='pending')
        except Payment.DoesNotExist:
            return Response({'error': "To'lov topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        note = request.data.get('note', '')
        payment.confirm(admin_note=note)

        notify_payment_confirmed.delay(payment.id)

        return Response({'message': "To'lov tasdiqlandi, obuna faollashdi!"})


class AdminPaymentRejectView(APIView):
    """Admin to'lovni rad etadi"""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id, status='pending')
        except Payment.DoesNotExist:
            return Response({'error': "To'lov topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        note = request.data.get('note', '')
        payment.reject(admin_note=note)

        notify_payment_rejected.delay(payment.id)

        return Response({'message': "To'lov rad etildi!"})


class AdminPendingPaymentsView(generics.ListAPIView):
    """Admin uchun — kutilayotgan to'lovlar"""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Payment.objects.filter(status='pending').order_by('-created_at')