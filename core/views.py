from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
import time

from authentication.utils import generate_receipt_pdf
from .models import Transaction, PaymentHistory
from authentication.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from core.serilizers import  *


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_view(request):
    data = request.data

    phone = data.get('phoneNumber')
    network = data.get('network')
    amount = data.get('amount')
    fee_type = data.get('feeType')

    if not phone or not network or not amount or not fee_type:
        return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        amount = float(amount)
    except ValueError:
        return Response({'error': 'Invalid amount format'}, status=status.HTTP_400_BAD_REQUEST)

    time.sleep(2)
    payment_reference = f"MP{uuid.uuid4().hex[:10].upper()}"

    try:
        transaction = Transaction(
            student=request.user,
            amount=amount,
            payment_type=fee_type,
            payment_method='mobile_money',
            status='pending'
        )
        transaction.full_clean()
        transaction.save()

        PaymentHistory.objects.create(
            transaction=transaction,
            student=request.user,
            amount=amount,
            date_paid=timezone.now()
        )

        fee_structure = request.user.fee_structures.last()
        pending = {}
        if fee_structure:
            pending = fee_structure.get_pending_payments()

        # Optional: Send notification to WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "chat__room1",
            {
                "type": "send_message",
                "message": "New Transaction made successfully!",
            }
        )

        return Response({
            "message": "Payment processed",
            "reference": payment_reference,
            "amount": amount,
            "feeType": fee_type,
            "network": network,
            "phoneNumber": phone,
            "transactionId": transaction.id,
            "status": transaction.status,
            "pending_payments": pending
        }, status=status.HTTP_200_OK)

    except ValidationError as ve:
        return Response(
            {"error": ve.message_dict if hasattr(ve, 'message_dict') else str(ve)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": f"Something went wrong: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_payments(request):
    user = request.user
    fee_structure = user.fee_structures.last()

    if not fee_structure:
        return Response({"detail": "No fee structure found for this user."}, status=status.HTTP_404_NOT_FOUND)

    pending_payments = {}

    fee_info = {
        'tuition': {
            'required': fee_structure.tuition_fee,
            'due_date': fee_structure.tuition_due_date
        },
        'hostel': {
            'required': fee_structure.hostel_fee,
            'due_date': fee_structure.hostel_due_date
        },
        'other': {
            'required': fee_structure.other_fee,
            'due_date': fee_structure.other_due_date
        }
    }

    for fee_type, info in fee_info.items():
        paid = fee_structure.get_paid_by_type(fee_type)
        balance = info['required'] - paid

        if balance > 0:
            pending_payments[fee_type] = {
                "amount": round(balance, 2),
                "due_date": info['due_date']  # Will return ISO date format or null
            }

    return Response({"pending_payments": pending_payments}, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_completed_transactions(request):
    user = request.user
    completed_transactions = user.transactions.filter(status='completed').order_by('-transaction_date')
    serializer = TransactionSerializer(completed_transactions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_fee_stats(request):
    user = request.user
    fee_structure = user.fee_structures.last()

    if not fee_structure:
        return Response({"detail": "No fee structure found for this user."}, status=status.HTTP_404_NOT_FOUND)

    total_required = fee_structure.total_fee
    total_paid = fee_structure.get_total_paid()
    outstanding = fee_structure.get_balance()

    return Response({
        "total_fee_required": round(total_required, 2),
        "total_paid": round(total_paid, 2),
        "outstanding_balance": round(outstanding, 2)
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_transactions(request):
    transactions = Transaction.objects.order_by('-transaction_date')[:5]
    data = [
        {
            "id": tx.id,
            "student_name": tx.student.full_name,
            "student_id": tx.student.student_id,
            "payment_type": tx.payment_type,
            "amount": str(tx.amount),
            "date": tx.transaction_date.strftime('%Y-%m-%d'),
            "status": tx.status
        }
        for tx in transactions
    ]
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transactions(request):
    transactions = Transaction.objects.order_by('-transaction_date')
    data = [
        {
            "id": tx.id,
            "student_name": tx.student.full_name,
            "student_id": tx.student.student_id,
            "payment_type": tx.payment_type,
            "amount": str(tx.amount),
            "date": tx.transaction_date.strftime('%Y-%m-%d'),
            "status": tx.status
        }
        for tx in transactions
    ]
    return Response(data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_payment_history(request):
    histories = PaymentHistory.objects.all().order_by('-date_paid')
    serializer = PaymentHistorySerializer(histories, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)