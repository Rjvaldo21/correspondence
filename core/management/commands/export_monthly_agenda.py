from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import IncomingLetter
import csv, os

class Command(BaseCommand):
    help = "Export Buku Agenda Karta Tama bulan ini ke CSV"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        qs = IncomingLetter.objects.filter(created_at__year=now.year, created_at__month=now.month)
        fn = f"agenda_incoming_{now.strftime('%Y_%m')}.csv"
        with open(fn, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["Agenda","Subject","Origin","Status","Created"])
            for o in qs: w.writerow([o.agenda_number,o.subject,o.origin,o.status,o.created_at])
        self.stdout.write(self.style.SUCCESS(f"Export OK: {os.path.abspath(fn)}"))
