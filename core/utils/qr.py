import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

def make_qr_png(data: str) -> ContentFile:
    """Return ContentFile PNG untuk disimpan ke ImageField."""
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return ContentFile(buf.getvalue())
