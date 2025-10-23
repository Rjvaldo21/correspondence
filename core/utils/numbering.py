from django.utils import timezone
from django.db import transaction
from django.db.models import Max
from core.models import IncomingLetter, OutgoingLetter
import time

def _year() -> int:
    return timezone.now().year

@transaction.atomic
def generate_agenda_number() -> str:
    """
    Format: AGD/<YEAR>/<6-digit>
    Strategi:
      - Ambil urutan terbesar yg ada (per tahun), lalu +1.
      - Jika bentrok (jarang tapi mungkin saat concurrency tinggi), cek exists & retry cepat.
    """
    y = _year()
    prefix = f"AGD/{y}/"

    # Ambil kandidat urutan berikutnya
    last = (IncomingLetter.objects
            .filter(agenda_number__startswith=prefix)
            .order_by("-agenda_number")
            .first())
    last_seq = 0
    if last and last.agenda_number:
        try:
            last_seq = int(last.agenda_number.split("/")[-1])
        except Exception:
            last_seq = 0

    # Coba hingga 5x kalau kebetulan bentrok
    for attempt in range(5):
        cand = f"{prefix}{last_seq + 1 + attempt:06d}"
        if not IncomingLetter.objects.filter(agenda_number=cand).exists():
            return cand
        time.sleep(0.01)  # jeda sangat singkat

    # Fallback darurat (amat jarang terpakai)
    ts = timezone.now().strftime("%H%M%S")  # 6 digit
    return f"{prefix}{ts}"

@transaction.atomic
def generate_outgoing_number(prefix: str = "ST") -> str:
    """
    Format: <PREFIX>/<YEAR>/<5-digit>
    Catatan:
      - Prefix sebaiknya salah satu dari ND/UD/ST/MM/LN (DOC_KIND).
      - Default 'ST' agar konsisten dgn pilihan model.
    """
    prefix = (prefix or "ST").upper()
    y = _year()
    base = f"{prefix}/{y}/"

    last = (OutgoingLetter.objects
            .filter(number__startswith=base)
            .order_by("-number")
            .first())
    last_seq = 0
    if last and last.number:
        try:
            last_seq = int(last.number.split("/")[-1])
        except Exception:
            last_seq = 0

    for attempt in range(5):
        cand = f"{base}{last_seq + 1 + attempt:05d}"
        if not OutgoingLetter.objects.filter(number=cand).exists():
            return cand
        time.sleep(0.01)

    # Fallback darurat
    ts = timezone.now().strftime("%H%M%S")  # 6 digit
    return f"{base}{ts[:5]}"  # tetap 5 digit
