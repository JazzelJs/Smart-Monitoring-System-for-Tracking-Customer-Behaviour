from django.core.management.base import BaseCommand
from datetime import date, timedelta
from backend_app.models import UserCafe, Report

class Command(BaseCommand):
    help = "Generate reports for the previous month"

    def handle(self, *args, **kwargs):
        today = date.today()
        first_of_this_month = today.replace(day=1)
        last_month = first_of_this_month - timedelta(days=1)
        year, month = last_month.year, last_month.month

        cafes = UserCafe.objects.all()
        for cafe in cafes:
            report, created = Report.objects.get_or_create(
                cafe=cafe,
                year=year,
                month=month,
                defaults={"file_url": None}  # Or generate a PDF and set the URL
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Report created for {cafe.name} - {year}-{month}"))
            else:
                self.stdout.write(f"Report already exists for {cafe.name} - {year}-{month}")
