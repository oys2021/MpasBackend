from django.db import models
from authentication.models import User

class Transaction(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('tuition', 'Tuition'),
        ('hostel', 'Hostel'),
        ('other', 'Other'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('mobile_money', 'Mobile Money'),
        ('bank', 'Bank'),
        ('card', 'Card'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction({self.id}) - {self.student.full_name}"


class PaymentHistory(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='payment_history')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_histories')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateTimeField(auto_now_add=True)
    receipt_url = models.URLField(blank=True)

    def __str__(self):
        return f"PaymentHistory({self.id})"
