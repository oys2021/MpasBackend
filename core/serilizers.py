# serializers.py
from rest_framework import serializers
from core.models import *
from authentication.serializers import StudentDetailSerializer



class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['status', 'transaction_date']


# class PaymentHistorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PaymentHistory
#         fields = '__all__'
#         read_only_fields = ['date_paid']


  # adjust import if needed

class PaymentHistorySerializer(serializers.ModelSerializer):
    student = StudentDetailSerializer(read_only=True)  # <-- use this

    class Meta:
        model = PaymentHistory
        fields = ['id', 'amount', 'date_paid', 'transaction', 'student']



