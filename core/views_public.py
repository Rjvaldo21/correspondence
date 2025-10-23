from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import Http404

from .models import IncomingLetter, OutgoingLetter

SAFE_PREFIXES_OUT = ("ST/", "ND/", "UD/", "MM/", "LN/")

def verify_document(request, code: str):
    """
    Halaman verifikasi publik berdasarkan kode:
    - Incoming:  AGD/YYYY/NNNNNN  (agenda_number)
    - Outgoing:  ST|ND|UD|MM|LN/YYYY/NNNNNN  (number)
    Menampilkan metadata minimum (tanpa konten).
    """
    now = timezone.now()
    ctx = {"code": code, "now": now, "kind": None, "obj": None}

    if code.startswith("AGD/"):
        o = get_object_or_404(IncomingLetter, agenda_number=code)
        ctx["kind"] = "incoming"
        ctx["obj"] = {
            "agenda_number": o.agenda_number,
            "status": o.get_status_display(),
            "created_at": o.created_at,
            "priority": o.get_priority_display(),
        }
        return render(request, "public/verify.html", ctx)

    if code.startswith(SAFE_PREFIXES_OUT):
        o = get_object_or_404(OutgoingLetter, number=code)
        ctx["kind"] = "outgoing"
        ctx["obj"] = {
            "number": o.number,
            "status": o.get_status_display(),
            "created_at": o.created_at,
            "template": o.get_template_type_display(),
            "has_signed_pdf": bool(o.signed_pdf),
        }
        return render(request, "public/verify.html", ctx)

    raise Http404("Kode verifikasaun la válidu.")
