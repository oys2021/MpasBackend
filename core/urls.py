from django.urls import path
from core import views


urlpatterns=[
    path('payments/', views.payment_view, name='payment'),
    path('payments/pending/', views.get_pending_payments, name='get-pending-payments'),
    path('transactions/completed/', views.get_completed_transactions, name='get-completed-transactions'),
    path('fees/stats/', views.get_fee_stats, name='get-fee-stats'),
]