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
            # "receiptUrl": f"https://example.com/receipts/{payment_reference}"
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
