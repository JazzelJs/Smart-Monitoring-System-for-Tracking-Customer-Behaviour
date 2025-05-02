from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from random import randint, choice
from backend_app.models import (
    UserCafe, Floor, Camera, Seat, Customer,
    EntryEvent, SeatDetection, PopularSeat, PeakHour
)
from django.utils import timezone

class Command(BaseCommand):
    help = "Generate dummy data for April 2025 for all cafes"

    def handle(self, *args, **kwargs):
        local_tz = timezone.get_current_timezone()

        for cafe in UserCafe.objects.all():
            # Create Floors & Cameras
            for floor_num in range(1, 3):
                floor, _ = Floor.objects.get_or_create(cafe=cafe, floor_number=floor_num)
                for cam_num in range(1, 3):
                    Camera.objects.get_or_create(
                        cafe=cafe,
                        floor=floor,
                        channel=f"Channel {cam_num}",
                        status="active",
                        ip_address=f"10.0.{floor_num}.{cam_num}"
                    )

            # Create Seats
            for i in range(1, 11):
                Seat.objects.get_or_create(
                    cafe=cafe,
                    chair_index=i,
                    x1=randint(0, 100), y1=randint(0, 100),
                    x2=randint(100, 200), y2=randint(100, 200)
                )

            # Create Customers
            import uuid

            for _ in range(5):
                status = choice(["new", "returning"])
                first_visit = timezone.make_aware(datetime(2025, 3, randint(1, 31), 12, 0), local_tz)
                face_id = f"{cafe.id}_april_{uuid.uuid4().hex[:8]}"
                Customer.objects.create(
                    face_id=face_id,
                    cafe=cafe,
                    first_visit=first_visit,
                    visit_count=randint(1, 10),
                    average_stay=randint(20, 60),
                    status=status,
                    last_visit=timezone.now(),
        )


            # Entry Events (April 2025)
            camera = Camera.objects.filter(cafe=cafe).first()
            for day in range(1, 31):  # April has 30 days
                is_weekend = (datetime(2025, 4, day).weekday() >= 5)  # Saturday or Sunday
                visitors = randint(25, 45) if is_weekend else randint(15, 30)
                for _ in range(visitors):
                    hour = choice([9, 10, 11, 13, 15, 16, 17])  # Slightly shifted hours
                    timestamp = timezone.make_aware(datetime(2025, 4, day, hour, randint(0, 59)), local_tz)
                    EntryEvent.objects.create(
                        camera=camera,
                        event_type=choice(["enter", "exit"]),
                        timestamp=timestamp
                    )

            # Seat Detections
            for _ in range(60):
                day = randint(1, 30)
                hour = choice([9, 11, 13, 15, 17])
                start_time = timezone.make_aware(datetime(2025, 4, day, hour, 0), local_tz)
                seat = Seat.objects.filter(cafe=cafe).order_by('?').first()
                SeatDetection.objects.create(
                    camera=camera,
                    seat=seat,
                    time_start=start_time,
                    time_end=start_time + timedelta(minutes=randint(15, 90))
                )

            # Popular Seats
            for seat in Seat.objects.filter(cafe=cafe):
                PopularSeat.objects.get_or_create(
                    cafe=cafe, seat=seat,
                    defaults={"usage_count": randint(5, 20), "avg_duration": randint(20, 60)}
                )

            # Peak Hour
            detector = SeatDetection.objects.filter(camera__cafe=cafe).first()
            if detector:
                peak_start = timezone.make_aware(datetime(2025, 4, 14, 11, 0), local_tz).time()
                peak_end = timezone.make_aware(datetime(2025, 4, 14, 12, 0), local_tz).time()
                PeakHour.objects.get_or_create(
                    cafe=cafe,
                    detector=detector,
                    defaults={
                        "start_time": peak_start,
                        "end_time": peak_end,
                        "current_occupancy": randint(60, 95),
                        "avg_daily_visitors": randint(25, 50)
                    }
                )

        self.stdout.write(self.style.SUCCESS("April 2025 dummy data created successfully for all cafes!"))
