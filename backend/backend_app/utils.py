import random
from .models import EmailOTP
from django.core.mail import send_mail
from django.conf import settings

def generate_otp(email, purpose="signup"):
    otp = str(random.randint(100000, 999999))  # store as string
    EmailOTP.objects.create(email=email, code=otp, purpose=purpose)
    return otp

def send_otp_via_email(email, otp):
    subject = "Your OTP Code"
    message = f"Your verification code is: {otp}"
    print(f"[OTP] Sending {otp} to {email}")  # Optional debug log
    send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
