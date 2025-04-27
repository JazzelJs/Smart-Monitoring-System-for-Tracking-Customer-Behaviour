import os
from django.conf import settings
from datetime import datetime
from .models import EntryEvent, SeatDetection
from reportlab.pdfgen import canvas

def generate_pdf_for_month(cafe, year, month):
    # Gather dummy summary data (adjust as needed)
    total_visitors = EntryEvent.objects.filter(camera__cafe=cafe, timestamp__year=year, timestamp__month=month, event_type='enter').count()
    avg_visit_duration = SeatDetection.objects.filter(camera__cafe=cafe, time_start__year=year, time_start__month=month).count()  # Dummy

    # Generate PDF
    file_name = f"report_{cafe.id}_{year}_{month}.pdf"
    file_path = os.path.join(settings.MEDIA_ROOT, "reports", file_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    c = canvas.Canvas(file_path)
    c.drawString(100, 800, f"Monthly Report for {cafe.name} ({year}-{month})")
    c.drawString(100, 780, f"Total Visitors: {total_visitors}")
    c.drawString(100, 760, f"Average Visit Duration (Dummy): {avg_visit_duration}")
    c.save()

    return f"/media/reports/{file_name}"
