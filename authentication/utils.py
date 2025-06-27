
from django.core.mail import send_mail
from django.conf import settings

def send_email_notification(to_email, subject, html_message):
    send_mail(
        subject=subject,
        message='', 
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[to_email],
        html_message=html_message,
        fail_silently=False,
    )

# utils/receipt_generator.py
from reportlab.pdfgen import canvas
from django.conf import settings
import os
import uuid

def generate_receipt_pdf(transaction, user):
    filename = f"receipt_{transaction.id}_{uuid.uuid4().hex[:6]}.pdf"
    receipt_path = os.path.join(settings.MEDIA_ROOT, 'receipts', filename)
    os.makedirs(os.path.dirname(receipt_path), exist_ok=True)

    c = canvas.Canvas(receipt_path)
    c.setFont("Helvetica", 14)
    c.drawString(100, 800, "Payment Receipt")
    c.setFont("Helvetica", 10)
    c.drawString(100, 770, f"Name: {user.full_name}")
    c.drawString(100, 750, f"Transaction ID: {transaction.id}")
    c.drawString(100, 730, f"Amount: GHS {transaction.amount}")
    c.drawString(100, 710, f"Payment Type: {transaction.payment_type}")
    c.drawString(100, 690, f"Payment Method: {transaction.payment_method}")
    c.drawString(100, 670, f"Date: {transaction.transaction_date.strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(100, 650, f"Status: {transaction.status}")
    c.save()

    return f"{settings.MEDIA_URL}receipts/{filename}"

