from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from random import randint, choice
from backend_app.models import UserCafe, Floor, Camera, Seat, Customer, EntryEvent, SeatDetection, PopularSeat, PeakHour
from django.contrib.auth import get_user_model
from django.utils import timezone

class Command(BaseCommand):
    help = "Generate dummy data for February 2025 with realistic patterns"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        user = User.objects.get(email="jasonglx856@gmail.com")  # ✅ Find specific user

        cafe = UserCafe.objects.get(name="Ngopi Pintar Cafe", user=user)  # ✅ Assign to specific cafe
        
        local_tz = timezone.get_current_timezone()

        # Floors and Cameras (reuse if already exist)
        for floor_num in range(1, 3):
            floor, _ = Floor.objects.get_or_create(cafe=cafe, floor_number=floor_num)
            for cam_num in range(1, 3):
                Camera.objects.get_or_create(cafe=cafe, floor=floor, channel=f"Channel {cam_num}", status="active", ip_address=f"192.168.1.{cam_num}")

        # Seats (reuse if already exist)
        for i in range(1, 11):
            Seat.objects.get_or_create(cafe=cafe, x1=randint(0, 100), y1=randint(0, 100), x2=randint(100, 200), y2=randint(100, 200))

        # Customers
        for i in range(5):
            status = choice(["new", "returning"])
            first_visit = timezone.make_aware(datetime(2025, 1, randint(1, 31), 12, 0), local_tz)  # First visit in January
            Customer.objects.get_or_create(
                face_id=f"face_feb_{i}",  # Distinguish face IDs
                cafe=cafe,
                defaults={
                    "first_visit": first_visit,
                    "visit_count": randint(1, 10),
                    "average_stay": randint(20, 60),
                    "status": status,
                }
            )

        # Entry Events (February 2025)
        for day in range(1, 29):  # February has 28 days
            is_weekend = (datetime(2025, 2, day).weekday() >= 4)  # Friday-Sunday
            visitors = randint(20, 40) if is_weekend else randint(5, 20)
            for _ in range(visitors):
                hour = choice([9, 10, 11, 12, 13, 15, 16, 17])
                local_dt = timezone.make_aware(datetime(2025, 2, day, hour, 0), local_tz)
                EntryEvent.objects.create(
                    camera=Camera.objects.filter(cafe=cafe).first(),
                    event_type=choice(["enter", "exit"]),
                    timestamp=local_dt
                )

        # Seat Detections (February 2025)
        for _ in range(40):
            day = randint(1, 28)
            hour = choice([9, 11, 13, 15, 17])
            start_time = timezone.make_aware(datetime(2025, 2, day, hour, 0), local_tz)
            SeatDetection.objects.create(
                camera=Camera.objects.filter(cafe=cafe).first(),
                chair_id=randint(1, 10),
                time_start=start_time,
                time_end=start_time + timedelta(minutes=randint(15, 90))
            )

        # Popular Seats
        for seat in Seat.objects.filter(cafe=cafe):
            PopularSeat.objects.get_or_create(
                cafe=cafe, seat=seat,
                defaults={"usage_count": randint(5, 15), "avg_duration": randint(20, 60)}
            )

        # Peak Hour (February 2025)
        peak_start_time = timezone.make_aware(datetime(2025, 2, 15, 11, 0), local_tz).time()
        peak_end_time = timezone.make_aware(datetime(2025, 2, 15, 12, 0), local_tz).time()
        PeakHour.objects.create(
            cafe=cafe,
            detector=SeatDetection.objects.filter(camera__cafe=cafe).first(),
            start_time=peak_start_time,
            end_time=peak_end_time,
            current_occupancy=75.0,  # Example: 75% occupancy
            avg_daily_visitors=28.0
        )

        self.stdout.write(self.style.SUCCESS("February 2025 dummy data created successfully!"))
