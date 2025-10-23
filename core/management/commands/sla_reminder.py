from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Disposition, DispositionAssignment

class Command(BaseCommand):
    help = "Reminder SLA disposisi (due_date mendekat/terlewati)"

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        warn = Disposition.objects.filter(due_date__isnull=False, due_date__lte=today).order_by("due_date")
        for d in warn:
            assignees = DispositionAssignment.objects.filter(disposition=d).values_list("assignee__username", flat=True)
            self.stdout.write(f"[REMINDER] Dispo {d.id} → due {d.due_date} → assignees={list(assignees)}")
        self.stdout.write(self.style.SUCCESS("SLA reminder selesai."))
