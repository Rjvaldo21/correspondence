from io import BytesIO
from django.core.files.base import ContentFile
from barcode import Code128
from barcode.writer import ImageWriter

def make_code128_png(data: str) -> ContentFile:
    """Return ContentFile PNG barcode Code128 untuk ImageField."""
    buf = BytesIO()
    Code128(data, writer=ImageWriter()).write(buf)
    return ContentFile(buf.getvalue())
