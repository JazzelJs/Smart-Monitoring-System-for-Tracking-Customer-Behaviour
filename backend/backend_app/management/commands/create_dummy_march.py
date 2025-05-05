from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from random import randint, choice
from backend_app.models import (
    UserCafe, Floor, Camera, Seat,
    Customer, EntryEvent, SeatDetection,
    PopularSeat, PeakHour
)
from django.utils import timezone
import uuid

class Command(BaseCommand):
    help = "Generate dummy data for March 2025 with realistic patterns for all cafes"

    def handle(self, *args, **kwargs):
        local_tz = timezone.get_current_timezone()

        for cafe in UserCafe.objects.all():
            # ✅ Skip if March data already exists
            has_march_data = EntryEvent.objects.filter(
                camera__cafe=cafe,
                timestamp__year=2025,
                timestamp__month=3
            ).exists() or SeatDetection.objects.filter(
                camera__cafe=cafe,
                time_start__year=2025,
                time_start__month=3
            ).exists()

            if has_march_data:
                self.stdout.write(f"Skipping {cafe.name} — March data already exists.")
                continue

            # Floors and Cameras
            for floor_num in range(1, 3):
                floor, _ = Floor.objects.update_or_create(
                    cafe=cafe,
                    floor_number=floor_num,
                    defaults={"name": f"Floor {floor_num}"}
                )

                for cam_num in range(1, 3):
                    Camera.objects.update_or_create(
                        cafe=cafe,
                        floor=floor,
                        channel=f"Channel {cam_num}",
                        defaults={
                            "status": "active",
                            "ip_address": f"192.168.{floor_num}.{cam_num}"
                        }
                    )

            # Seats (by chair_index)
            for i in range(1, 11):
                Seat.objects.update_or_create(
                    cafe=cafe,
                    chair_index=i,
                    defaults={
                        "x1": randint(0, 100),
                        "y1": randint(0, 100),
                        "x2": randint(100, 200),
                        "y2": randint(100, 200)
                    }
                )

            # Customers
            for _ in range(5):
                status = choice(["new", "returning"])
                first_visit = timezone.make_aware(datetime(2025, 2, randint(1, 28), 12, 0), local_tz)
                face_id = f"{cafe.id}_march_{uuid.uuid4().hex[:8]}"
                Customer.objects.create(
                    face_id=face_id,
                    cafe=cafe,
                    first_visit=first_visit,
                    visit_count=randint(1, 10),
                    average_stay=randint(20, 60),
                    status=status,
                    last_visit=timezone.now()
                )

            # Entry Events (March 2025)
            camera = Camera.objects.filter(cafe=cafe).first()
            for day in range(1, 29):
                is_weekend = (datetime(2025, 3, day).weekday() >= 4)
                visitors = randint(30, 50) if is_weekend else randint(10, 30)
                for _ in range(visitors):
                    hour = choice([10, 11, 12, 13, 14, 16, 17, 18])
                    local_dt = timezone.make_aware(datetime(2025, 3, day, hour, 0), local_tz)
                    EntryEvent.objects.create(
                        camera=camera,
                        event_type=choice(["enter", "exit"]),
                        timestamp=local_dt
                    )

            # Seat Detections
            for _ in range(50):
                day = randint(1, 28)
                hour = choice([10, 12, 14, 16, 18])
                start_time = timezone.make_aware(datetime(2025, 3, day, hour, 0), local_tz)
                seat = Seat.objects.filter(cafe=cafe).order_by('?').first()
                SeatDetection.objects.create(
                    camera=camera,
                    seat=seat,
                    time_start=start_time,
                    time_end=start_time + timedelta(minutes=randint(15, 90))
                )

            # Popular Seats
            for seat in Seat.objects.filter(cafe=cafe):
                PopularSeat.objects.update_or_create(
                    cafe=cafe,
                    seat=seat,
                    defaults={
                        "usage_count": randint(5, 15),
                        "avg_duration": randint(20, 60)
                    }
                )

            # Peak Hour
            detector = SeatDetection.objects.filter(camera__cafe=cafe).first()
            if detector:
                peak_start_time = timezone.make_aware(datetime(2025, 3, 15, 12, 0), local_tz).time()
                peak_end_time = timezone.make_aware(datetime(2025, 3, 15, 13, 0), local_tz).time()
                PeakHour.objects.update_or_create(
                    cafe=cafe,
                    detector=detector,
                    defaults={
                        "start_time": peak_start_time,
                        "end_time": peak_end_time,
                        "current_occupancy": randint(60, 90),
                        "avg_daily_visitors": randint(20, 50)
                    }
                )

            self.stdout.write(self.style.SUCCESS(f"Dummy data created for {cafe.name}"))

        self.stdout.write(self.style.SUCCESS("✅ Done! Only new cafes without March data were seeded."))
