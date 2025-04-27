from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
import datetime

# --- AUTH & USER ---

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email
    
class EmailOTP(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    purpose = models.CharField(
        max_length=20,
        choices=[("signup", "Signup"), ("reset", "Reset")],
        default="signup"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"{self.email} - {self.code} ({self.purpose})"


# --- CORE DATA MODELS ---

class UserCafe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cafes')
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    capacity = models.IntegerField()

    def __str__(self):
        return self.name

# models.py
from django.db import models

class Seat(models.Model):
    seat_id = models.AutoField(primary_key=True)
    cafe = models.ForeignKey('UserCafe', on_delete=models.CASCADE, related_name="seats")
    last_updated = models.DateTimeField(auto_now=True)
    is_occupied = models.BooleanField(default=False)
    x1 = models.IntegerField()
    y1 = models.IntegerField()
    x2 = models.IntegerField()
    y2 = models.IntegerField()

    def __str__(self):
        return f"Seat {self.seat_id} in {self.cafe.name}"


class Floor(models.Model):
    cafe = models.ForeignKey(UserCafe, on_delete=models.CASCADE, related_name="floors")
    floor_number = models.IntegerField()
    name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Cafe {self.cafe} -- Floor {self.floor_number} - {self.cafe.name}"


class Camera(models.Model):
    id = models.AutoField(primary_key=True)
    cafe = models.ForeignKey(UserCafe, on_delete=models.CASCADE, related_name="cameras")
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name="cameras")
    status = models.CharField(max_length=50, choices=[("active", "Active"), ("inactive", "Inactive")])
    location = models.CharField(max_length=255, null=True, blank=True)
    last_active = models.DateTimeField(null=True, blank=True)
    channel = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    admin_name = models.CharField(max_length=100, blank=True)
    admin_password = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Camera {self.id} in {self.cafe.name}"

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    cafe = models.ForeignKey('UserCafe', on_delete=models.CASCADE, related_name="customers")  # 🔥 Add this line
    face_id = models.CharField(max_length=100, unique=True)  # Link to face embeddings
    first_visit = models.DateTimeField()
    visit_count = models.IntegerField(default=0)
    last_visit = models.DateTimeField(null=True, blank=True)
    average_stay = models.FloatField()
    status = models.CharField(max_length=50, choices=[("new", "New"), ("returning", "Returning")])

    def __str__(self):
        return f"Customer {self.customer_id} - Cafe {self.cafe.name}"


class SeatDetection(models.Model):
    camera = models.ForeignKey('Camera', on_delete=models.CASCADE, related_name='detections')  # NEW
    chair_id = models.IntegerField()
    time_start = models.DateTimeField()
    time_end = models.DateTimeField(null=True, blank=True)

    def duration(self):
        if self.time_start and self.time_end:
            return (self.time_end - self.time_start).total_seconds()
        return None

    def __str__(self):
        return f"Camera {self.camera.id} - Chair {self.chair_id} - {self.time_start.strftime('%Y-%m-%d %H:%M:%S')}"



class EntryEvent(models.Model):
    camera = models.ForeignKey(Camera, null=True, blank=True, on_delete=models.SET_NULL)
    EVENT_CHOICES = [('enter', 'Enter'), ('exit', 'Exit')]
    event_type = models.CharField(max_length=5, choices=EVENT_CHOICES)
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(default=timezone.now)
    track_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.event_type} at {self.timestamp}"


class HourlyEntrySummary(models.Model):
    hour_block = models.DateTimeField(unique=True)
    entered = models.PositiveIntegerField(default=0)
    exited = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.hour_block.strftime('%Y-%m-%d %H:%M')} | Entered: {self.entered}, Exited: {self.exited}"

 
   

class PopularSeat(models.Model):
    
    cafe = models.ForeignKey(UserCafe, on_delete=models.CASCADE, related_name="popular_seats")
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name="popularity")
    usage_count = models.IntegerField(default=0)
    avg_duration = models.FloatField()

    def __str__(self):
        return f"Popular Seat {self.seat.seat_id} in {self.cafe.name}"

class PeakHour(models.Model):
    
    cafe = models.ForeignKey(UserCafe, on_delete=models.CASCADE, related_name="peak_hours")
    detector = models.ForeignKey(SeatDetection, on_delete=models.CASCADE, related_name="peak_hours")
    start_time = models.TimeField()
    end_time = models.TimeField()
    current_occupancy = models.FloatField()
    avg_daily_visitors = models.FloatField()

    def __str__(self):
        return f"Peak Hour {self.start_time} - {self.end_time} in {self.cafe.name}"



class Report(models.Model):
    cafe = models.ForeignKey(UserCafe, on_delete=models.CASCADE, related_name="reports")
    year = models.IntegerField()
    month = models.IntegerField()
    file_url = models.URLField(null=True, blank=True)  # Optional PDF
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cafe', 'year', 'month')  # Ensure one report per month

    def __str__(self):
        return f"Report {self.year}-{self.month} for {self.cafe.name}"


    def __str__(self):
        return f"Report {self.year}-{self.month} for {self.cafe.name}"
class ActivityLog(models.Model):
    
    cafe = models.ForeignKey(UserCafe, on_delete=models.CASCADE, related_name="activity_logs")
    seat_detection = models.ForeignKey(SeatDetection, on_delete=models.CASCADE, related_name="activity_logs")
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    ACTIVITY_TYPE = [
    ("seating", "Seating"),
    ("entry", "Entry"),
    ("exit", "Exit"),
]

    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE, default="seating")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Activity {self.activity_type} at {self.timestamp}"

class Notification(models.Model):
    
    cafe = models.ForeignKey(UserCafe, on_delete=models.CASCADE, related_name="notifications")
    peak_hour = models.ForeignKey(PeakHour, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    seat_detection = models.ForeignKey(SeatDetection, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    message = models.TextField()
    category = models.CharField(max_length=50, choices=[("info", "Info"), ("alert", "Alert")])
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification {self.notification_id} for {self.cafe.name}"
