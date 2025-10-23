from __future__ import annotations
import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.conf import settings
from urllib.parse import urljoin

from core.models import IncomingLetter, OutgoingLetter
from core.utils.numbering import generate_agenda_number, generate_outgoing_number
from core.utils.qr import make_qr_png
from core.utils.barcode import make_code128_png

logger = logging.getLogger(__name__)

def _verify_base() -> str:
    """
    Ambil base URL verifikasi publik.
    - Jika kamu punya domain publik, set di settings:
        PUBLIC_BASE_URL = "https://sistem.tic.gov.tl"
        PUBLIC_VERIFY_PATH = "/verify/"
        maka hasil final: https://sistem.tic.gov.tl/verify/<kode>
    - Jika tidak, fallback "/verify/" → jadinya path relatif saja.
    """
    public_base = getattr(settings, "PUBLIC_BASE_URL", "")  
    verify_path = getattr(settings, "PUBLIC_VERIFY_PATH", "/verify/")
    if not verify_path.endswith("/"):
        verify_path += "/"
    return urljoin(public_base, verify_path)

# ========== SURAT MASUK ==========

@receiver(pre_save, sender=IncomingLetter)
def incoming_pre_save(sender, instance: IncomingLetter, **kwargs):
    if not instance.agenda_number:
        instance.agenda_number = generate_agenda_number()

@receiver(post_save, sender=IncomingLetter)
def incoming_post_save(sender, instance: IncomingLetter, created: bool, **kwargs):
    """
    Generate QR (link verifikasi publik) & barcode (berbasis agenda_number) sekali saja.
    """
    try:
        if instance.qr_image and instance.barcode_image:
            return

        # URL verifikasi publik menggunakan nomor agenda (stabil)
        if instance.agenda_number and not instance.qr_image:
            url = _verify_base() + instance.agenda_number
            qr = make_qr_png(url)  # -> ContentFile
            instance.qr_image.save(f"qr_in_{instance.pk}.png", qr, save=False)

        # Barcode pakai nomor agenda
        if instance.agenda_number and not instance.barcode_image:
            bc = make_code128_png(instance.agenda_number)  # -> ContentFile
            instance.barcode_image.save(f"bc_in_{instance.pk}.png", bc, save=False)

        if instance.qr_image or instance.barcode_image:
            instance.save(update_fields=["qr_image", "barcode_image"])

    except Exception as e:
        logger.exception("Gagal generate QR/Barcode surat masuk id=%s: %s", instance.pk, e)

# ========== SURAT KELUAR ==========

@receiver(pre_save, sender=OutgoingLetter)
def outgoing_pre_save(sender, instance: OutgoingLetter, **kwargs):
    """
    Saat status FINAL & number kosong → generate (lock).
    Prefix mengikuti template_type (ND/UD/ST/MM/LN), fallback 'ST' bila kosong.
    """
    if instance.status == "FINAL" and not instance.number:
        prefix = (instance.template_type or "ST").upper()
        instance.number = generate_outgoing_number(prefix=prefix)

@receiver(post_save, sender=OutgoingLetter)
def outgoing_post_save(sender, instance: OutgoingLetter, created: bool, **kwargs):
    """
    Generate QR ke halaman verifikasi publik (sekali saja) pakai number.
    """
    try:
        if instance.qr_image or not instance.number:
            return

        url = _verify_base() + instance.number
        qr = make_qr_png(url)
        instance.qr_image.save(f"qr_out_{instance.pk}.png", qr, save=False)
        instance.save(update_fields=["qr_image"])

    except Exception as e:
        logger.exception("Gagal generate QR surat keluar id=%s: %s", instance.pk, e)