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


# Popular seats
from collections import defaultdict

def get_zone(cx, cy, grid_size=100):
    return f"{cx // grid_size}_{cy // grid_size}"

def compute_zone_counts(detections, grid_size=100):
    zone_counts = defaultdict(int)
    for det in detections:
        if det.centroid_x is not None and det.centroid_y is not None:
            zone = get_zone(det.centroid_x, det.centroid_y, grid_size)
            zone_counts[zone] += 1
    sorted_zones = sorted(zone_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"zone": z, "count": c} for z, c in sorted_zones]
