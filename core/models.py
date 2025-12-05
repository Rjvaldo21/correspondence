import os
from django.db import models
from django.contrib.auth.models import Group, User
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import Group as DjangoGroup, User as DjangoUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

# ========== UPLOAD HELPERS (HARUS SEBELUM KELAS MODEL) ==========
def _slugged_path(base, filename, length=60):
    name, ext = os.path.splitext(filename)
    safe = slugify(name)[:length] or "file"
    ext = (ext or "").lower()[:10]
    return f"{base}/{timezone.now():%Y/%m}/{safe}{ext}"

def upload_incoming_scan(instance, filename):
    return _slugged_path("incoming/scans", filename)

def upload_outgoing_signed(instance, filename):
    return _slugged_path("outgoing/signed", filename)

def upload_attachment_file(instance, filename):
    return _slugged_path("attachments", filename)

# ---------- Choice constants (Tetun/PT) ----------
PRIORITY = (
    ("B",  "Normal"),
    ("S",  "Urgente"),
    ("SS", "Muito Urgente"),
)

LETTER_STATUS = (
    ("DRAFT", "Draft"),
    ("REG",   "Rejistu"),
    ("PROG",  "Iha Prosesu"),
    ("DONE",  "Remata"),
    ("ARCH",  "Arkivu"),
)

OUT_STATUS = (
    ("DRAFT",    "Draft"),
    ("APPROVED", "Aprovadu"),
    ("FINAL",    "Final"),
    ("SENT",     "Manda Ona"),
    ("ARCH",     "Arkivu"),
)


DOC_KIND = (
    ("ND", "Nota Servisu"),
    ("UD", "Konvite"),
    ("ST", "Karta Servisu"),
    ("MM", "Memo"),
    ("LN", "Seluk"),
)

RECEIVED_VIA = (
    ("fisik", "Fíziku"),
    ("email", "Email"),
)

class ClassificationTag(models.Model):
    name = models.CharField("Naran Klasifikasaun", max_length=100, unique=True)
    class Meta:
        verbose_name = "Klasifikasaun"
        verbose_name_plural = "Klasifikasaun"
        ordering = ["name"]
    def __str__(self): return self.name

class Attachment(models.Model):
    title = models.CharField("Titulu", max_length=200)
    file = models.FileField(
        "Ficheiru",
        upload_to=upload_attachment_file,
        max_length=255,
    )
    uploaded_by = models.ForeignKey(
        User, verbose_name="Hatutun husi",
        on_delete=models.SET_NULL, null=True, blank=True
    )
    uploaded_at = models.DateTimeField("Data Hatutu", auto_now_add=True)
    class Meta:
        verbose_name = "Anexu"
        verbose_name_plural = "Anexu"
        ordering = ["-uploaded_at"]
    def __str__(self): return self.title

# ---------- Karta Tama ----------
class IncomingLetter(models.Model):
    received_via = models.CharField("Tama via", max_length=10, choices=RECEIVED_VIA, default="fisik")
    origin = models.CharField("Karta Husi", max_length=255)
    origin_number = models.CharField("Númeru Karta", max_length=100)
    origin_date = models.DateField("Data Karta")
    subject = models.CharField("Asuntu", max_length=300)
    priority = models.CharField("Prioridade", max_length=2, choices=PRIORITY, default="B")

    attachments = models.ManyToManyField(Attachment, verbose_name="Anexu", blank=True)
    scan_pdf = models.FileField(
        "Scan PDF",
        upload_to=upload_incoming_scan,
        max_length=255,
        validators=[FileExtensionValidator(["pdf"])],
        help_text="Rezultadu skaneamuntu (PDF)",
        blank=True,  # jadikan wajib dengan menghapus blank=True jika perlu
    )
    classification_tags = models.ManyToManyField(ClassificationTag, verbose_name="Klasifikasaun", blank=True)

    agenda_number = models.CharField(
        "Númeru Agenda", max_length=30, unique=True, blank=True,
        help_text="Hari'i automátiku bainhira rejistu primeiru."
    )
    barcode_image = models.ImageField("Kódigu Barra", upload_to="incoming/barcodes/", blank=True)
    qr_image = models.ImageField("QR Kode", upload_to="incoming/qrcodes/", blank=True)

    status = models.CharField("Estado", max_length=5, choices=LETTER_STATUS, default="REG")
    current_handler = models.ForeignKey(
        User, verbose_name="Responsável (agora)",
        on_delete=models.SET_NULL, null=True, blank=True, related_name="handling_letters"
    )

    created_by = models.ForeignKey(
        User, verbose_name="Rejista husi",
        on_delete=models.SET_NULL, null=True, blank=True, related_name="incoming_created"
    )
    created_at = models.DateTimeField("Kria iha", auto_now_add=True)
    updated_at = models.DateTimeField("Atualiza iha", auto_now=True)

    # Retensaun/Arquivo
    retention_class = models.CharField("Klas Retensaun", max_length=50, blank=True, help_text="Kode retensaun (JRA, dll.)")
    retention_until = models.DateField("To'o data", null=True, blank=True)
    disposed_at = models.DateField("Data Arkivu", null=True, blank=True)

    class Meta:
        verbose_name = "Karta Tama"
        verbose_name_plural = "Karta Tama"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["agenda_number"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["origin_date"]),
        ]
    def __str__(self): return f"{self.agenda_number or '—'} — {self.subject}"
    @property
    def is_archived(self): return self.status == "ARCH"

class Disposition(models.Model):
    letter = models.ForeignKey(IncomingLetter, verbose_name="Karta", on_delete=models.CASCADE, related_name="dispositions")
    sender = models.ForeignKey(User, verbose_name="Hato'o husi", on_delete=models.SET_NULL, null=True, related_name="dispo_sent")
    note = models.TextField("Observasaun / Nota", blank=True)
    due_date = models.DateField("Data-limite", null=True, blank=True)
    allow_parallel = models.BooleanField("Paralelu?", default=True)
    parent = models.ForeignKey("self", verbose_name="Dispozisaun Aman", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    created_at = models.DateTimeField("Kria iha", auto_now_add=True)
    class Meta:
        verbose_name = "Despacho"
        verbose_name_plural = "Despacho"
        ordering = ["-created_at"]
    def __str__(self): return f"Dispo {self.id} — {self.letter.agenda_number or self.letter_id}"

class DispositionAssignment(models.Model):
    disposition = models.ForeignKey(Disposition, verbose_name="Dispozisaun", on_delete=models.CASCADE, related_name="assignments")
    assignee = models.ForeignKey(User, verbose_name="Destinatáriu / Responsável", on_delete=models.CASCADE, related_name="dispo_tasks")
    read_at = models.DateTimeField("Lee iha", null=True, blank=True)
    completed_at = models.DateTimeField("Kompleta iha", null=True, blank=True)
    class Meta:
        verbose_name = "Distribuisaun Dispozisaun"
        verbose_name_plural = "Agenda"
        unique_together = ("disposition", "assignee")
        ordering = ["assignee__username"]
    def __str__(self): return f"{self.assignee} ← Dispo {self.disposition_id}"

class FollowUp(models.Model):
    letter = models.ForeignKey(IncomingLetter, verbose_name="Karta", on_delete=models.CASCADE, related_name="followups")
    doc_type = models.CharField("Tipu Dokumentu", max_length=2, choices=DOC_KIND, default="ND")
    title = models.CharField("Titulu", max_length=200)
    file = models.FileField("Ficheiru", upload_to="incoming/followups/%Y/%m/")
    author = models.ForeignKey(User, verbose_name="Autor", on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField("Kria iha", auto_now_add=True)
    class Meta:
        verbose_name = "Asaun Tuir Mai"
        verbose_name_plural = "Asaun Tuir Mai"
        ordering = ["-created_at"]
    def __str__(self): return f"{self.get_doc_type_display()} — {self.title}"

# ---------- Karta Sai ----------
class OutgoingLetter(models.Model):
    template_type = models.CharField("Formuláriu", max_length=2, choices=DOC_KIND, default="ND")
    subject = models.CharField("Asuntu", max_length=300)
    body = models.TextField("Konteúdu")
    attachments = models.ManyToManyField(Attachment, verbose_name="Anexu", blank=True)

    number = models.CharField(
        "Númeru", max_length=40, unique=True, blank=True,
        help_text="Sei tau automátiku bainhira estadu FINAL (númeru rai)."
    )
    status = models.CharField("Estado", max_length=10, choices=OUT_STATUS, default="DRAFT")

    created_by = models.ForeignKey(User, verbose_name="Kria husi", on_delete=models.SET_NULL, null=True, related_name="out_created")
    created_at = models.DateTimeField("Kria iha", auto_now_add=True)
    updated_at = models.DateTimeField("Atualiza iha", auto_now=True)

    signed_pdf = models.FileField(
        "PDF Asina / TTE",
        upload_to=upload_outgoing_signed,
        max_length=255,
        validators=[FileExtensionValidator(["pdf"])],
        blank=True,
    )
    qr_image = models.ImageField("QR Kode", upload_to="outgoing/qrcodes/%Y/%m/", blank=True)

    retention_class = models.CharField("Klas Retensaun", max_length=50, blank=True)
    retention_until = models.DateField("To'o data", null=True, blank=True)

    class Meta:
        verbose_name = "Karta Sai"
        verbose_name_plural = "Karta Sai"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["number"]),
        ]
    def __str__(self): return f"{self.number or '—'} — {self.subject}"

class ReviewStep(models.Model):
    letter = models.ForeignKey(OutgoingLetter, verbose_name="Karta", on_delete=models.CASCADE, related_name="reviews")
    order = models.PositiveIntegerField("Passu #")
    reviewer = models.ForeignKey(User, verbose_name="Revisor / Paraf", on_delete=models.CASCADE)
    approved_at = models.DateTimeField("Aprova iha", null=True, blank=True)
    note = models.CharField("Observasaun", max_length=300, blank=True)
    class Meta:
        verbose_name = "Passu Revisaun"
        verbose_name_plural = "Passu Revisaun"
        unique_together = ("letter", "order")
        ordering = ["order"]
    def __str__(self): return f"Review #{self.order} ba {self.letter_id}"

# ---------- Ekspedisaun ----------
class ExpeditionRecord(models.Model):
    content_type = models.ForeignKey(ContentType, verbose_name="Tipu Kontentu", on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField("ID Objetu")
    content_object = GenericForeignKey("content_type", "object_id")

    method = models.CharField(
        "Metodu", max_length=20,
        choices=(("email", "Email"), ("fisik", "Fíziku")), default="email"
    )
    destination = models.CharField("Destino / Destinatáriu", max_length=255)
    sent_at = models.DateTimeField("Data Haruka", auto_now_add=True)
    received_by = models.CharField("Recebe husi", max_length=255, blank=True)
    received_at = models.DateTimeField("Data Simu", null=True, blank=True)
    proof_file = models.FileField("Prova / Evidénsia", upload_to="expedition/proofs/%Y/%m/", blank=True)

    class Meta:
        verbose_name = "Rejistu Ekspedisaun"
        verbose_name_plural = "Rejistu Ekspedisaun"
        ordering = ["-sent_at"]
    def __str__(self): return f"Ekspedisaun {self.id} → {self.destination}"

class PersuratanPortal(IncomingLetter):
    class Meta:
        proxy = True
        verbose_name = "Portal Karta (UI)"
        verbose_name_plural = "Portal Karta (UI)"
        ordering = ["-created_at"]


class Grupu(Group):
    class Meta:
        proxy = True
        verbose_name = "Grupu"
        verbose_name_plural = "Grupu"

class Uzuariu(User):
    class Meta:
        proxy = True
        verbose_name = "Uzuáriu"
        verbose_name_plural = "Uzuáriu"


class DestructionRecord(models.Model):
    tipu_konteúdu_id = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )

    objetu_id = models.PositiveIntegerField(db_column='object_id')

    content_object = GenericForeignKey("tipu_konteúdu_id", "objetu_id")

    reason = models.CharField("Razaun", max_length=255, blank=True)
    approved_by = models.ForeignKey(
        User, verbose_name="Aprova ona husi",
        on_delete=models.SET_NULL, null=True, blank=True
    )
    destroyed_at = models.DateField("Destroi iha", null=True, blank=True)
    document = models.FileField("Notisia (PDF)", upload_to="destruction/%Y/%m/", blank=True)

    class Meta:
        verbose_name = "Destruisaun Arkivu"
        verbose_name_plural = "Destruisaun Arkivu"
        ordering = ["-destroyed_at"]

    def __str__(self):
        return f"Pemusnahan {self.id} → {self.content_object}"