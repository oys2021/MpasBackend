from django.db import models
from django.core.exceptions import ValidationError
from authentication.models import User
from decimal import Decimal


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

    tuition_due_date = models.DateField(null=True, blank=True)
    hostel_due_date = models.DateField(null=True, blank=True)
    other_due_date = models.DateField(null=True, blank=True)

    total_fee = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.total_fee = self.tuition_fee + self.hostel_fee + self.other_fee
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.academic_year}"

    # def get_paid_by_type(self, fee_type):
    #     return self.student.transactions.filter(
    #         payment_type=fee_type, status__in=['pending', 'completed']  
    #     ).aggregate(total=models.Sum('amount'))['total'] or 0

    def get_paid_by_type(self, fee_type):
        return self.student.transactions.filter(
            payment_type=fee_type,
            status='completed'  # Only completed ones count
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    

    def get_pending_payments(self):
        return {
            'tuition': {
                'amount': float(self.tuition_fee - self.get_paid_by_type('tuition')),
                'due_date': self.tuition_due_date
            },
            'hostel': {
                'amount': float(self.hostel_fee - self.get_paid_by_type('hostel')),
                'due_date': self.hostel_due_date
            },
            'other': {
                'amount': float(self.other_fee - self.get_paid_by_type('other')),
                'due_date': self.other_due_date
            },
        }


    def get_total_paid(self):
        return sum(t.amount for t in self.student.transactions.filter(status='completed'))
    
    

    # def get_pending_payments(self):
    #     print("sellf tuition fee",self.tuition_fee)
    #     print("sellf get_paid_by_type",self.get_paid_by_type('tuition'))
    #     print("ress",float(self.tuition_fee - self.get_paid_by_type('tuition')))

    #     return {
    #         'tuition': float(self.tuition_fee - self.get_paid_by_type('tuition')),
    #         'hostel': float(self.hostel_fee - self.get_paid_by_type('hostel')),
    #         'other': float(self.other_fee - self.get_paid_by_type('other')),
    #     }


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

        if latest_fee_structure.is_fee_type_paid(self.payment_type):
            raise ValidationError(f"{self.payment_type.capitalize()} fee has already been fully paid.")

        required_for_type = {
            'tuition': latest_fee_structure.tuition_fee,
            'hostel': latest_fee_structure.hostel_fee,
            'other': latest_fee_structure.other_fee
        }.get(self.payment_type, Decimal('0.00'))

        # 🟡 Now check what has been paid so far
        already_paid = latest_fee_structure.get_paid_by_type(self.payment_type)
        remaining = required_for_type - already_paid

        # ✅ Enforce full remaining payment (no more, no less)
        
        if self.amount != remaining:
            print(self.amount)
            print(remaining)
            raise ValidationError({
                "amount": [f"You must pay the full remaining amount of GHS {remaining:.2f} for {self.payment_type}. You already paid GHS {already_paid:.2f}."]
            })

        # ✅ Optional: prevent overpaying total fee
        total_paid = latest_fee_structure.get_total_paid()
        if (total_paid + self.amount) > latest_fee_structure.total_fee:
            raise ValidationError("This payment would exceed the total required fees.")






    def save(self, *args, **kwargs):
        self.full_clean()
        self.status = 'completed'
        super().save(*args, **kwargs)  

    


    def __str__(self):
        return f"Transaction({self.id}) - {self.student.full_name}"

    


class PaymentHistory(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='payment_history')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_histories')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PaymentHistory({self.id})"
