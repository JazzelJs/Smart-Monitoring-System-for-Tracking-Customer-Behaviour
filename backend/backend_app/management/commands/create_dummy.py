from django.core.management.base import BaseCommand
from datetime import datetime, timedelta, timezone as dt_timezone
from random import randint, choice
from backend_app.models import UserCafe, Floor, Camera, Seat, Customer, EntryEvent, SeatDetection, PopularSeat, PeakHour
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Generate dummy data for March 2025 with realistic patterns"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        user = User.objects.get(email="jasonglx856@gmail.com")  # ✅ Find specific user

        cafe = UserCafe.objects.get(name="Ngopi Pintar Cafe", user=user)  # ✅ Assign to specific cafe
        
        # Floors and Cameras
        for floor_num in range(1, 3):
            floor, _ = Floor.objects.get_or_create(cafe=cafe, floor_number=floor_num)
            for cam_num in range(1, 3):
                Camera.objects.get_or_create(cafe=cafe, floor=floor, channel=f"Channel {cam_num}", status="active", ip_address=f"192.168.1.{cam_num}")

        # Seats
        for i in range(1, 11):
            Seat.objects.get_or_create(cafe=cafe, x1=randint(0, 100), y1=randint(0, 100), x2=randint(100, 200), y2=randint(100, 200))

        # Customers
        for i in range(5):
            status = choice(["new", "returning"])
            Customer.objects.get_or_create(
                face_id=f"face_{i}",
                cafe=cafe,
                defaults={
                    "first_visit": datetime(2025, 2, randint(1, 28), 12, 0, tzinfo=dt_timezone.utc),
                    "visit_count": randint(1, 10),
                    "average_stay": randint(20, 60),
                    "status": status,
                }
            )

        # Entry Events (March 2025) - Simulate busy weekends
        for day in range(1, 32):  # Full March
            is_weekend = (datetime(2025, 3, day).weekday() >= 4)  # Friday-Sunday
            visitors = randint(30, 50) if is_weekend else randint(10, 30)
            for _ in range(visitors):
                hour = choice([10, 11, 12, 13, 14, 16, 17, 18])  # Peak hours
                EntryEvent.objects.create(
                    camera=Camera.objects.filter(cafe=cafe).first(),
                    event_type=choice(["enter", "exit"]),
                    timestamp=datetime(2025, 3, day, hour, 0, tzinfo=dt_timezone.utc)
                )

        # Seat Detections (March 2025)
        for _ in range(50):
            day = randint(1, 31)
            hour = choice([10, 12, 14, 16, 18])
            start_time = datetime(2025, 3, day, hour, 0, tzinfo=dt_timezone.utc)
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

        # Peak Hour (March 2025)
        PeakHour.objects.create(
            cafe=cafe,
            detector=SeatDetection.objects.filter(camera__cafe=cafe).first(),
            start_time=datetime(2025, 3, 15, 12, 0, tzinfo=dt_timezone.utc).time(),  # 12-1 PM
            end_time=datetime(2025, 3, 15, 13, 0, tzinfo=dt_timezone.utc).time(),
            current_occupancy=80.0,  # Example: 80% occupancy
            avg_daily_visitors=35.0
        )

        self.stdout.write(self.style.SUCCESS("March 2025 dummy data created successfully!"))
