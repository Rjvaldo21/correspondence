from django.contrib import admin, messages
from django.contrib.contenttypes.admin import GenericTabularInline
from django.http import HttpResponse
from .models import DestructionRecord
from django import forms
import csv
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib.admin.sites import NotRegistered
from .models import PersuratanPortal
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.contrib.auth.models import Group as AuthGroup, User as AuthUser
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.admin.sites import NotRegistered
from .models import Grupu, Uzuariu
from django.utils import timezone  
from .utils_retention import compute_retention_until  

try:
    admin.site.unregister(PersuratanPortal)
except NotRegistered:
    pass

from .models import (
    ClassificationTag, Attachment,
    IncomingLetter, Disposition, DispositionAssignment, FollowUp,
    OutgoingLetter, ReviewStep,
    ExpeditionRecord, PersuratanPortal,
)

# ============================================================
# Proxy & perbaikan autocomplete ke auth.User/auth.Group
# ============================================================
# Lepas admin bawaan (kalau masih terpasang)
for _m in (AuthGroup, AuthUser):
    try:
        admin.site.unregister(_m)
    except NotRegistered:
        pass

@admin.register(DestructionRecord)
class DestructionRecordAdmin(admin.ModelAdmin):
    list_display = ("content_object","reason","approved_by","destroyed_at")
    search_fields = ("reason",)
    list_filter = ("destroyed_at",)
    autocomplete_fields = ("approved_by",)    

# Tampilkan proxy berlabel Tetun di sidebar
@admin.register(Grupu)
class GrupuAdmin(GroupAdmin):
    pass

@admin.register(Uzuariu)
class UzuariuAdmin(UserAdmin):
    pass

# Daftarkan ulang model dasar agar autocomplete_fields berfungsi,
# tapi sembunyikan dari menu admin.
@admin.register(AuthUser)
class _HiddenAuthUserAdmin(UserAdmin):
    search_fields = ("username", "first_name", "last_name", "email")
    def has_module_permission(self, request): return False
    def get_model_perms(self, request): return {}

@admin.register(AuthGroup)
class _HiddenAuthGroupAdmin(GroupAdmin):
    def has_module_permission(self, request): return False
    def get_model_perms(self, request): return {}
# ============================================================


# =========================
# Helper: preview image
# =========================
def _img_preview(filefield, height=80):
    if not filefield:
        return "—"
    try:
        url = filefield.url
        return mark_safe(f'<img src="{url}" height="{height}" />')
    except Exception:
        return "—"


# =========================
# Generic Inline Ekspedisi + Actions Export
# =========================

# --- Form kustom: widget tanggal, placeholder, accept PDF, dll. ---
class IncomingLetterForm(forms.ModelForm):
    class Meta:
        model = IncomingLetter
        fields = "__all__"
        widgets = {
            "origin_date": forms.DateInput(attrs={"type": "date"}),
            "subject": forms.TextInput(attrs={"placeholder": "Asuntu / Assunto…"}),
            "origin": forms.TextInput(attrs={"placeholder": "Oríjém Karta…"}),
            "scan_pdf": forms.ClearableFileInput(attrs={"accept": "application/pdf"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Kecilkan “noise” help text bawaan
        self.fields["classification_tags"].help_text = ""
        # Kelas util agar gaya input nyambung ke CSS kamu
        for name in ("origin", "origin_number", "subject"):
            self.fields[name].widget.attrs.update({"class": "of-input"})


class ExpeditionInline(GenericTabularInline):
    model = ExpeditionRecord
    extra = 0
    readonly_fields = ("sent_at",)
    fields = ("method","destination","sent_at","received_by","received_at","proof_file")

def export_agenda_csv(modeladmin, request, queryset):
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = "attachment; filename=agenda_incoming.csv"
    w = csv.writer(resp)
    w.writerow(["Agenda","Subject","Origin","Priority","Status","Created"])
    for o in queryset:
        w.writerow([o.agenda_number, o.subject, o.origin, o.get_priority_display(), o.get_status_display(), o.created_at])
    return resp
export_agenda_csv.short_description = "Export CSV (Buku Agenda Karta Tama)"

def export_outgoing_csv(modeladmin, request, queryset):
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = "attachment; filename=agenda_outgoing.csv"
    w = csv.writer(resp)
    w.writerow(["Number","Subject","Template","Status","Created"])
    for o in queryset:
        w.writerow([o.number, o.subject, o.get_template_type_display(), o.get_status_display(), o.created_at])
    return resp
export_outgoing_csv.short_description = "Export CSV (Buku Agenda Karta Sai)"


# =========================
# Referensia Geral
# =========================
@admin.register(ClassificationTag)
class ClassificationTagAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["name"]
    ordering = ["name"]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("title", "uploaded_by", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("title", "uploaded_by__username", "uploaded_by__email")
    date_hierarchy = "uploaded_at"


# =========================
# Karta Tama
# =========================
class FollowUpInline(admin.TabularInline):
    model = FollowUp
    extra = 0
    fields = ("doc_type", "title", "file", "author", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)


# >>> Tambahan: DispositionInline <<<
class DispositionInline(admin.TabularInline):
    model = Disposition
    fields = ("sender", "due_date", "allow_parallel", "note")
    extra = 0
    show_change_link = True
    autocomplete_fields = ("sender",)


@admin.action(description="Tandai status: Selesai (DONE)")
def mark_done(modeladmin, request, queryset):
    updated = queryset.update(status="DONE")
    modeladmin.message_user(request, f"Ditandai DONE: {updated} item.")


@admin.action(description="Arsipkan (ARCH)")
def mark_archived(modeladmin, request, queryset):
    updated = queryset.update(status="ARCH")
    modeladmin.message_user(request, f"Diarsipkan: {updated} item.")


@admin.register(IncomingLetter)
class IncomingLetterAdmin(admin.ModelAdmin):
    # ⚠️ Pastikan TIDAK mengatur change_form_template agar ikut template bawaan Jazzmin
    form = IncomingLetterForm  # <<< Tambahkan form kustom
    list_display = (
        "agenda_number", "subject", "origin", "priority", "status_badge",
        "created_at", "qr_thumb", "barcode_thumb",
    )
    list_filter = ("priority", "status", "created_at", "classification_tags")
    search_fields = ("agenda_number", "subject", "origin", "origin_number")
    date_hierarchy = "created_at"
    list_per_page = 25
    filter_horizontal = ("classification_tags", "attachments")
    autocomplete_fields = ("current_handler", "created_by")
    inlines = [DispositionInline, FollowUpInline, ExpeditionInline]  # <<< Tambahkan DispositionInline
    save_on_top = True
    actions = [mark_done, mark_archived, export_agenda_csv, "print_label"]

    readonly_fields = (
        "agenda_number", "qr_preview", "barcode_preview",
        "created_at", "updated_at",
        "quick_actions",  # tombol/teks akselerator di panel kanan
    )

    # ✅ Grid 2 kolom untuk fieldset pertama (hanya di halaman form model ini)
    fieldsets = (
        ("Metadadus Karta", {
            "classes": ("of-grid-2", "of-meta"),  # 2 kolom
            "fields": (
                ("received_via", "priority"),
                ("origin",),                         # full width
                ("origin_number", "origin_date"),
                "subject",                           # full width
            )
        }),
        ("Dokumentu", {
            "classes": ("of-grid-2", "of-docs"),    # 2 kolom
            "fields": ("scan_pdf", "attachments", "classification_tags"),
        }),
        ("Numerasaun & Rotulajen", {
            "classes": ("of-grid-2", "of-numera"),  # 2 kolom
            "fields": (("agenda_number",), ("qr_preview", "barcode_preview")),
        }),
        ("Estatus & Responsavel", {
    "classes": ("of-status",),  # cukup satu kelas (nanti CSS yang grid-kan)
    "fields": (
        ("status",),            # ⟵ BARIS SENDIRI
        ("current_handler",),   # ⟵ BARIS SENDIRI
        ("created_by", "created_at", "updated_at"),  # 3 kolom
        "quick_actions",        # full width
    ),
}),

        ("Retensaun Arkivu (opsional)", {
            "classes": ("collapse", "of-grid-2", "of-retention"),
            "fields": (("retention_class", "retention_until"), "disposed_at"),
        }),
    )

    # ⬇️ Media: muat CSS hanya untuk halaman change_form model ini
    class Media:
        css = {"all": ("of/correspondence-form.css",)}

    # ——— Optional helper untuk readonly "quick_actions"
    def quick_actions(self, obj=None):
        if not obj:
            return "-"
        return mark_safe(
            '<div class="of-qa">'
            f'<a class="button" href="../{obj.pk}/history/">History</a> '
            f'<a class="button" href="../{obj.pk}/change/?_continue=1">Save & Continue</a>'
            "</div>"
        )
    quick_actions.short_description = "Aksi Cepat"

    # contoh action extra yang sudah kamu daftarkan sebagai string
    def print_label(self, request, queryset):
        # isi sendiri sesuai url/logic cetak label
        self.message_user(request, f"Print label untuk {queryset.count()} data")

    # ======== BADGE STATUS (untuk list_display) ========
    @admin.display(description="Status")
    def status_badge(self, obj):
        css = {
            "DRAFT": "badge-draft",
            "REG":   "badge-reg",
            "DISP":  "badge-disp",
            "PROG":  "badge-prog",
            "DONE":  "badge-done",
            "ARCH":  "badge-arch",
        }.get(obj.status, "badge-draft")
        return format_html('<span class="badge badge-status {}">{}</span>', css, obj.get_status_display())

    # Thumbs for list view
    @admin.display(description="QR")
    def qr_thumb(self, obj):
        return _img_preview(obj.qr_image, height=50)

    @admin.display(description="Barcode")
    def barcode_thumb(self, obj):
        return _img_preview(obj.barcode_image, height=35)

    # Big preview for detail
    @admin.display(description="QR Preview")
    def qr_preview(self, obj):
        return _img_preview(obj.qr_image, height=120)

    @admin.display(description="Barcode Preview")
    def barcode_preview(self, obj):
        return _img_preview(obj.barcode_image, height=80)

    # ======== Aksi cepat sebagai readonly field (ganti object-tools kustom) ========
    @admin.display(description="Aksi Cepat")
    def quick_actions(self, obj):
        if not obj or not obj.pk:
            return "—"
        url_done = reverse("admin:core_incomingletter_mark_done", args=[obj.pk])
        url_arch = reverse("admin:core_incomingletter_mark_arch", args=[obj.pk])
        url_disp = reverse("admin:core_incomingletter_disposition", args=[obj.pk])
        url_fup  = reverse("admin:core_incomingletter_followup", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">✔️ Tandai DONE</a> '
            '<a class="button" href="{}">📦 Arsipkan</a> '
            '<a class="button" href="{}">➡️ Buat Disposisi</a> '
            '<a class="button" href="{}">➕ Follow Up</a>',
            url_done, url_arch, url_disp, url_fup
        )

    # ======== CUSTOM URL AKSI CEPAT DI CHANGE FORM ========
    def get_urls(self):
        urls = super().get_urls()
        my = [
            path(
                "<path:object_id>/mark-done/",
                self.admin_site.admin_view(self.mark_done_view),
                name="core_incomingletter_mark_done",
            ),
            path(
                "<path:object_id>/mark-arch/",
                self.admin_site.admin_view(self.mark_arch_view),
                name="core_incomingletter_mark_arch",
            ),
            path(
                "<path:object_id>/disposition/",
                self.admin_site.admin_view(self.goto_disposition),
                name="core_incomingletter_disposition",
            ),
            path(
                "<path:object_id>/followup/",
                self.admin_site.admin_view(self.goto_followup),
                name="core_incomingletter_followup",
            ),
        ]
        return my + urls

    def mark_done_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        obj.status = "DONE"
        obj.save(update_fields=["status"])
        messages.success(request, "Surat ditandai Selesai (DONE).")
        return redirect(reverse("admin:core_incomingletter_change", args=[obj.pk]))

    def mark_arch_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        obj.status = "ARCH"
        tag = obj.classification_tags.first()
        if tag and not obj.retention_until:
            obj.retention_until = compute_retention_until(tag.name, obj.created_at.date())
        obj.disposed_at = timezone.now().date()
        obj.save(update_fields=["status","retention_until","disposed_at"])
        messages.success(request, "Surat diarsipkan (ARCH) & retensi di-set.")
        return redirect(reverse("admin:core_incomingletter_change", args=[obj.pk]))

    def goto_disposition(self, request, object_id):
        return redirect("admin_disposition_create", pk=object_id)

    def goto_followup(self, request, object_id):
        return redirect("admin_followup_create", pk=object_id)

    # ======== ACTION: Cetak Label (Barcode + QR) ========
    @admin.action(description="Cetak Label (Barcode + QR)")
    def print_label(self, request, queryset):
        # HTML ringan untuk printer label (58mm). Gambar diambil dari field ImageField (barcode/qr).
        items = []
        for o in queryset:
            num = o.agenda_number or "—"
            subj = (o.subject or "")[:48]
            bc = o.barcode_image.url if o.barcode_image else ""
            qr = o.qr_image.url if o.qr_image else ""
            items.append(f"""
<div class="lbl">
  <div class="num">{num}</div>
  <div class="imgs">
    {f'<img class="bc" src="{bc}" />' if bc else ''}
    {f'<img class="qr" src="{qr}" />' if qr else ''}
  </div>
  <div class="subj">{subj}</div>
</div>
""")
        html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Labels</title>
<style>
@media print {{
  @page {{ size: 58mm auto; margin: 2mm; }}
  body {{ margin:0 }}
}}
body {{ font:12px/1.2 -apple-system,Segoe UI,Roboto,Arial; }}
.lbl {{ width:58mm; border:1px dashed #ccc; padding:4px; margin:6px auto; }}
.num {{ font-weight:700; font-size:12px; text-align:center; }}
.imgs {{ display:flex; align-items:center; justify-content:space-between; gap:4px; }}
.bc {{ max-width:42mm; height:auto; }}
.qr {{ width:14mm; height:14mm; }}
.subj {{ font-size:10px; margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
</style></head>
<body>
{''.join(items) if items else '<p>Tidak ada data.</p>'}
<script>window.print()</script>
</body></html>"""
        return HttpResponse(html)

    # --- RBAC RHS: sembunyikan & batasi akses surat ber-tag "RHS" ---
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related("classification_tags")
        if request.user.is_superuser:
            return qs
        if not request.user.groups.filter(name="RHS_ACCESS").exists():
            return qs.exclude(classification_tags__name__iexact="RHS")
        return qs

    def has_view_permission(self, request, obj=None):
        ok = super().has_view_permission(request, obj)
        if not ok or not obj:
            return ok
        if obj.classification_tags.filter(name__iexact="RHS").exists():
            return request.user.is_superuser or request.user.groups.filter(name="RHS_ACCESS").exists()
        return True


# Disposisi & Assignment admin
class DispositionAssignmentInline(admin.TabularInline):
    model = DispositionAssignment
    extra = 0
    autocomplete_fields = ("assignee",)
    readonly_fields = ("read_at", "completed_at")


@admin.register(Disposition)
class DispositionAdmin(admin.ModelAdmin):
    list_display = ("id", "letter_agenda", "sender", "due_date", "allow_parallel", "parent", "created_at")
    list_filter = ("allow_parallel", "created_at", "due_date")
    search_fields = ("letter__agenda_number", "sender__username", "sender__email")
    date_hierarchy = "created_at"
    autocomplete_fields = ("letter", "sender", "parent")
    inlines = [DispositionAssignmentInline]

    @admin.display(description="Agenda")
    def letter_agenda(self, obj):
        return getattr(obj.letter, "agenda_number", obj.letter_id)


@admin.register(DispositionAssignment)
class DispositionAssignmentAdmin(admin.ModelAdmin):
    list_display = ("disposition", "assignee", "read_at", "completed_at")
    search_fields = ("disposition__letter__agenda_number", "assignee__username", "assignee__email")
    list_filter = ("read_at", "completed_at")
    autocomplete_fields = ("disposition", "assignee")


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ("letter", "doc_type", "title", "author", "created_at")
    search_fields = ("title", "letter__agenda_number", "author__username", "author__email")
    list_filter = ("doc_type", "created_at")
    date_hierarchy = "created_at"
    autocomplete_fields = ("letter", "author")


# =========================
# Surat Keluar
# =========================
class ReviewStepInline(admin.TabularInline):
    model = ReviewStep
    extra = 0
    fields = ("order", "reviewer", "approved_at", "note")
    autocomplete_fields = ("reviewer",)


@admin.action(description="Set status → REVIEW")
def set_review(modeladmin, request, queryset):
    updated = queryset.update(status="REVIEW")
    modeladmin.message_user(request, f"Status REVIEW: {updated} item.")


@admin.action(description="Set status → APPROVED")
def set_approved(modeladmin, request, queryset):
    updated = queryset.update(status="APPROVED")
    modeladmin.message_user(request, f"Status APPROVED: {updated} item.")


@admin.action(description="Set status → FINAL (lock nomor)")
def set_final(modeladmin, request, queryset):
    updated = queryset.update(status="FINAL")
    modeladmin.message_user(request, f"Status FINAL (nomor akan terisi via signal): {updated} item.")


@admin.action(description="Set status → MANDA")
def set_sent(modeladmin, request, queryset):
    updated = queryset.update(status="MANDA")
    modeladmin.message_user(request, f"Status MANDA: {updated} item.")


@admin.action(description="Arsipkan (ARCH)")
def set_arch(modeladmin, request, queryset):
    updated = queryset.update(status="ARCH")
    modeladmin.message_user(request, f"Status ARCH: {updated} item.")


@admin.register(OutgoingLetter)
class OutgoingLetterAdmin(admin.ModelAdmin):
    # (FIX) Hapus change_form_template agar pakai template bawaan Jazzmin
    list_display = ("number", "subject", "template_type", "status_badge", "created_at", "qr_thumb")
    list_filter = ("template_type", "status", "created_at")
    search_fields = ("number", "subject", "created_by__username", "created_by__email")
    date_hierarchy = "created_at"
    list_per_page = 25
    inlines = [ReviewStepInline, ExpeditionInline]
    autocomplete_fields = ("created_by",)
    save_on_top = True
    actions = [set_review, set_approved, set_final, set_sent, set_arch, export_outgoing_csv]

    readonly_fields = ("number", "qr_preview", "created_at", "updated_at", "status_actions")

    fieldsets = (
        ("Informasaun Karta", {
            "fields": (("template_type", "subject"), "body", "attachments")
        }),
        ("Númeru & Asinatura Eletrónika", {
            "fields": (("number", "qr_preview"), "signed_pdf")
        }),
        ("Estatus & Auditoria", {
            "fields": (
                ("status", "created_by"),
                ("created_at", "updated_at"),
                # (NEW) tombol aksi status
                "status_actions",
            )
        }),
        ("Retensaun (opsional)", {
            "classes": ("collapse",),
            "fields": (("retention_class", "retention_until"),),
        }),
    )

    @admin.display(description="Status")
    def status_badge(self, obj):
        css = {
            "DRAFT": "badge-draft",
            "REVIEW": "badge-review",
            "APPROVED": "badge-approved",
            "FINAL": "badge-final",
            "MANDA": "badge-sent",
            "ARCH": "badge-arch",
        }.get(obj.status, "badge-draft")
        return format_html('<span class="badge badge-status {}">{}</span>', css, obj.get_status_display())

    @admin.display(description="QR")
    def qr_thumb(self, obj):
        return _img_preview(obj.qr_image, height=50)

    @admin.display(description="QR Preview")
    def qr_preview(self, obj):
        return _img_preview(obj.qr_image, height=120)

    # ======== Aksi status sebagai readonly field (ganti object-tools kustom) ========
    @admin.display(description="Transisi Status")
    def status_actions(self, obj):
        if not obj or not obj.pk:
            return "—"
        to = lambda s: reverse(f"admin:core_outgoingletter_to_{s.lower()}", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">REVIEW</a> '
            '<a class="button" href="{}">APPROVED</a> '
            '<a class="button" href="{}">FINAL</a> '
            '<a class="button" href="{}">MANDA</a> '
            '<a class="button" href="{}">ARCH</a>',
            to("REVIEW"), to("APPROVED"), to("FINAL"), to("SENT"), to("ARCH"),
        )

    # ======== CUSTOM URL TRANSISI STATUS ========
    def get_urls(self):
        urls = super().get_urls()
        my = [
            path("<path:object_id>/status/REVIEW/",   self.admin_site.admin_view(self.to_review),   name="core_outgoingletter_to_review"),
            path("<path:object_id>/status/APPROVED/", self.admin_site.admin_view(self.to_approved), name="core_outgoingletter_to_approved"),
            path("<path:object_id>/status/FINAL/",    self.admin_site.admin_view(self.to_final),    name="core_outgoingletter_to_final"),
            path("<path:object_id>/status/SENT/",     self.admin_site.admin_view(self.to_sent),     name="core_outgoingletter_to_sent"),
            path("<path:object_id>/status/ARCH/",     self.admin_site.admin_view(self.to_arch),     name="core_outgoingletter_to_arch"),
        ]
        return my + urls

    def _jump(self, request, object_id, status, msg):
        obj = self.get_object(request, object_id)

        # Enforce alur
        if status == "APPROVED" and not obj.reviews.exists():
            messages.error(request, "Tidak bisa APPROVED: belum ada ReviewStep.")
            return redirect(reverse("admin:core_outgoingletter_change", args=[obj.pk]))

        if status == "FINAL":
            steps = list(obj.reviews.all())
            if steps and any(s.approved_at is None for s in steps):
                messages.error(request, "Tidak bisa FINAL: masih ada ReviewStep yang belum approved.")
                return redirect(reverse("admin:core_outgoingletter_change", args=[obj.pk]))

        obj.status = status
        obj.save(update_fields=["status"])
        messages.success(request, msg)
        return redirect(reverse("admin:core_outgoingletter_change", args=[obj.pk]))

    def to_review(self, request, object_id):   return self._jump(request, object_id, "REVIEW",   "Status → REVIEW")
    def to_approved(self, request, object_id): return self._jump(request, object_id, "APPROVED", "Status → APPROVED")
    def to_final(self, request, object_id):    return self._jump(request, object_id, "FINAL",    "Status → FINAL (Nomor terkunci)")
    def to_sent(self, request, object_id):     return self._jump(request, object_id, "MANDA",     "Status → SENT")
    def to_arch(self, request, object_id):     return self._jump(request, object_id, "ARCH",     "Status → ARCH")


@admin.register(ReviewStep)
class ReviewStepAdmin(admin.ModelAdmin):
    list_display = ("letter", "order", "reviewer", "approved_at", "note")
    list_filter = ("approved_at",)
    search_fields = ("letter__number", "letter__subject", "reviewer__username", "reviewer__email")
    autocomplete_fields = ("letter", "reviewer")


# =========================
# Ekspedisi
# =========================
@admin.register(ExpeditionRecord)
class ExpeditionRecordAdmin(admin.ModelAdmin):
    list_display = ("content_object", "method", "destination", "sent_at", "received_by", "received_at")
    list_filter = ("method", "sent_at", "received_at")
    search_fields = ("destination", "received_by")
    date_hierarchy = "sent_at"


# =========================
# Portal ke UI Persuratan (sidebar item)
# =========================
# @admin.register(PersuratanPortal)
# class PersuratanPortalAdmin(admin.ModelAdmin):
#     change_list_template = "admin/portal_redirect.html"
#
#     # Langsung arahkan ke UI persuratan embedded
#     def changelist_view(self, request, extra_context=None):
#         return redirect("admin_home")  # atau "admin_incoming_list"
