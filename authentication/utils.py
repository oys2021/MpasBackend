
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
