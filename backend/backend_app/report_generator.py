import os
from django.conf import settings
from datetime import datetime
from django.db.models import ExpressionWrapper, F, DurationField,Sum,Avg
from .models import EntryEvent, SeatDetection
from reportlab.pdfgen import canvas

def generate_pdf_for_month(cafe, year, month):
    # === Gather summary data ===
    total_visitors = EntryEvent.objects.filter(
        camera__cafe=cafe,
        timestamp__year=year,
        timestamp__month=month,
        event_type='enter'
    ).count()

    # === Average visit duration ===
    detections = SeatDetection.objects.filter(
        camera__cafe=cafe,
        time_start__year=year,
        time_start__month=month,
        time_end__isnull=False
    )

    durations = detections.annotate(
    duration=ExpressionWrapper(F('time_end') - F('time_start'), output_field=DurationField())
)

    avg_duration = durations.aggregate(avg=Avg('duration'))['avg'] if durations.exists() else None

    # === Popular seat (based on longest total duration) ===

    seat_stats = durations.values('seat__seat_id').annotate(
    total_duration=Sum('duration')
).order_by('-total_duration').first()

    popular_seat = f"Chair {seat_stats['seat__seat_id']}" if seat_stats else "-"

    # === Generate PDF ===
    file_name = f"report_{cafe.id}_{year}_{month}.pdf"
    file_path = os.path.join(settings.MEDIA_ROOT, "reports", file_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    c = canvas.Canvas(file_path)
    c.drawString(100, 800, f"Monthly Report for {cafe.name} ({year}-{month})")
    c.drawString(100, 780, f"Total Visitors: {total_visitors}")
    c.drawString(100, 760, f"Average Visit Duration: {str(avg_duration) if avg_duration else '0'}")
    c.drawString(100, 740, f"Most Popular Seat: {popular_seat}")
    c.save()

    return f"/media/reports/{file_name}"
