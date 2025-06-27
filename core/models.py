from django.db import models
from django.core.exceptions import ValidationError
from authentication.models import User

class ProgramFee(models.Model):
    program = models.CharField(max_length=100)
    level = models.CharField(max_length=10) 
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    hostel_fee = models.DecimalField(max_digits=10, decimal_places=2)
    other_fee = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('program', 'level')

    def __str__(self):
        return f"{self.program} - Level {self.level}"


class FeeStructure(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.CharField(max_length=20)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    hostel_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    other_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.total_fee = self.tuition_fee + self.hostel_fee + self.other_fee
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.academic_year}"

    def get_total_paid(self):
        return sum(t.amount for t in self.student.transactions.filter(status='completed'))

    def get_paid_by_type(self, fee_type):
        return self.student.transactions.filter(
            payment_type=fee_type, status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    def get_balance(self):
        return self.total_fee - self.get_total_paid()

    def is_fully_paid(self):
        return self.get_total_paid() >= self.total_fee

    def is_fee_type_paid(self, fee_type):
        required = {
            'tuition': self.tuition_fee,
            'hostel': self.hostel_fee,
            'other': self.other_fee
        }.get(fee_type, 0)
        paid = self.get_paid_by_type(fee_type)
        return paid >= required



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
    installment_number = models.PositiveIntegerField(null=True, blank=True)

    def clean(self):
        latest_fee_structure = self.student.fee_structures.last()
        if not latest_fee_structure:
            raise ValidationError("No fee structure assigned to this student.")

        paid_for_type = self.student.transactions.filter(
            payment_type=self.payment_type, status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        required_for_type = {
            'tuition': latest_fee_structure.tuition_fee,
            'hostel': latest_fee_structure.hostel_fee,
            'other': latest_fee_structure.other_fee
        }.get(self.payment_type, 0)

        remaining = required_for_type - paid_for_type

        if self.status == 'completed' and self.amount != remaining:
            raise ValidationError(
                f"To mark this {self.payment_type} payment as completed, you must pay the exact remaining balance: {remaining:.2f}"
            )

        total_paid = sum(t.amount for t in self.student.transactions.filter(status='completed'))
        if (total_paid + self.amount) > latest_fee_structure.total_fee:
            raise ValidationError("This payment would exceed the total required fees.")

    def save(self, *args, **kwargs):
        self.full_clean() 

        if self.status == 'pending':
            latest_fee_structure = self.student.fee_structures.last()
            if latest_fee_structure:
                paid_for_type = self.student.transactions.filter(
                    payment_type=self.payment_type, status='completed'
                ).aggregate(total=models.Sum('amount'))['total'] or 0

                required_for_type = {
                    'tuition': latest_fee_structure.tuition_fee,
                    'hostel': latest_fee_structure.hostel_fee,
                    'other': latest_fee_structure.other_fee
                }.get(self.payment_type, 0)

                if self.amount == (required_for_type - paid_for_type):
                    self.status = 'completed'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Transaction({self.id}) - {self.student.full_name}"


class PaymentHistory(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='payment_history')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_histories')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateTimeField(auto_now_add=True)
    # receipt_url = models.URLField(blank=True)

    def __str__(self):
        return f"PaymentHistory({self.id})"
