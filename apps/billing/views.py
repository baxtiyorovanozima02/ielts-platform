from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
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

    @swagger_auto_schema(
        operation_summary="Planlar ro'yxati",
        operation_description="Barcha mavjud obuna planlarini ko'rish (Free va Premium)"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class UserSubscriptionView(generics.RetrieveAPIView):
    """Foydalanuvchining aktiv obunasi"""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Mening obunаm",
        operation_description="Foydalanuvchining hozirgi aktiv obunasini ko'rish"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        return Subscription.objects.filter(
            user=self.request.user,
            is_active=True
        ).first()


class PaymentCreateView(APIView):
    """Foydalanuvchi to'lov qilish"""
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="To'lov qilish",
        operation_description="Foydalanuvchi Premium obuna uchun to'lov yuboradi. Admin tasdiqlagan zahoti obuna faollashadi.",
        request_body=PaymentCreateSerializer,
        responses={
            201: openapi.Response("To'lov qabul qilindi"),
            400: openapi.Response("Xatolik"),
        }
    )

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

    @swagger_auto_schema(
        operation_summary="Mening to'lovlarim",
        operation_description="Foydalanuvchining barcha to'lovlari tarixi"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by('-created_at')


class AdminPaymentConfirmView(APIView):
    """Admin to'lovni tasdiqlaydi"""
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_summary="To'lovni tasdiqlash (Admin)",
        operation_description="Admin to'lovni tasdiqlaydi. Obuna avtomatik faollashadi va foydalanuvchiga email + Telegram xabar yuboriladi.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'note': openapi.Schema(type=openapi.TYPE_STRING, description='Admin izohi')
            }
        ),
        responses={
            200: openapi.Response("To'lov tasdiqlandi"),
            404: openapi.Response("To'lov topilmadi"),
        }
    )
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

    @swagger_auto_schema(
        operation_summary="To'lovni rad etish (Admin)",
        operation_description="Admin to'lovni rad etadi. Foydalanuvchiga email + Telegram xabar yuboriladi.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'note': openapi.Schema(type=openapi.TYPE_STRING, description='Rad etish sababi')
            }
        ),
        responses={
            200: openapi.Response("To'lov rad etildi"),
            404: openapi.Response("To'lov topilmadi"),
        }
    )
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

    @swagger_auto_schema(
        operation_summary="Kutilayotgan to'lovlar (Admin)",
        operation_description="Admin uchun — hali tasdiqlanmagan barcha to'lovlar ro'yxati"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Payment.objects.filter(status='pending').order_by('-created_at')