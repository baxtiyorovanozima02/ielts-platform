from django.urls import path
from .views import (
    SubscriptionPlanListView,
    UserSubscriptionView,
    PaymentCreateView,
    PaymentListView,
    AdminPaymentConfirmView,
    AdminPaymentRejectView,
    AdminPendingPaymentsView,
)

urlpatterns = [
    path('plans/', SubscriptionPlanListView.as_view(), name='subscription-plans'),
    path('my-subscription/', UserSubscriptionView.as_view(), name='my-subscription'),
    path('pay/', PaymentCreateView.as_view(), name='payment-create'),
    path('my-payments/', PaymentListView.as_view(), name='my-payments'),

    path('admin/payments/', AdminPendingPaymentsView.as_view(), name='admin-payments'),
    path('admin/payments/<int:payment_id>/confirm/', AdminPaymentConfirmView.as_view(), name='payment-confirm'),
    path('admin/payments/<int:payment_id>/reject/', AdminPaymentRejectView.as_view(), name='payment-reject'),
]
