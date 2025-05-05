from django.core.management.base import BaseCommand
from backend_app.models import Seat
from collections import defaultdict

class Command(BaseCommand):
    help = "Remove duplicate Seat entries (same cafe and chair_index), keeping only one per pair"

    def handle(self, *args, **kwargs):
        seen = defaultdict(list)

        for seat in Seat.objects.all():
            key = (seat.cafe_id, seat.chair_index)
            seen[key].append(seat)

        deleted_count = 0

        for key, duplicates in seen.items():
            if len(duplicates) > 1:
                # Keep the first, delete the rest
                to_delete = duplicates[1:]
                deleted_count += len(to_delete)
                for dupe in to_delete:
                    dupe.delete()
                self.stdout.write(f"✔ Removed {len(to_delete)} duplicate(s) for cafe_id={key[0]}, chair_index={key[1]}")

        self.stdout.write(self.style.SUCCESS(f"✅ Done. {deleted_count} duplicate seat(s) deleted."))
