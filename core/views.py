from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView
)

from .models import (
    IncomingLetter, Disposition, DispositionAssignment, FollowUp,
    OutgoingLetter
)
from .forms import (
    IncomingLetterForm, OutgoingLetterForm,
    DispositionForm, FollowUpForm
)

@login_required
def ui_home(request):
    # Arahkan ke halaman Portal UI yang kamu pakai.
    # Kalau kamu sudah punya named-url, ganti ke redirect("incoming_list")
    return redirect("/incoming/")

# =========================
# SURAT MASUK
# =========================

class IncomingList(LoginRequiredMixin, ListView):
    model = IncomingLetter
    paginate_by = 20
    ordering = ["-created_at"]
    template_name = "incoming/list.html"


class IncomingCreate(LoginRequiredMixin, CreateView):
    model = IncomingLetter
    form_class = IncomingLetterForm
    template_name = "incoming/form.html"
    success_url = reverse_lazy("incoming_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Karta tama rejista ho susesu.")
        return super().form_valid(form)


class IncomingUpdate(LoginRequiredMixin, UpdateView):
    model = IncomingLetter
    form_class = IncomingLetterForm
    template_name = "incoming/form.html"
    success_url = reverse_lazy("incoming_list")


class IncomingDetail(LoginRequiredMixin, DetailView):
    model = IncomingLetter
    template_name = "incoming/detail.html"


class DispositionCreate(LoginRequiredMixin, CreateView):
    """
    Create Disposition dari halaman Detail Surat Masuk.
    Form dipost dari incoming/detail.html (bukan halaman terpisah).
    Jika invalid, render kembali incoming/detail.html dan tampilkan error.
    """
    model = Disposition
    form_class = DispositionForm
    template_name = "incoming/detail.html"  

    def dispatch(self, request, *args, **kwargs):
        self.letter = get_object_or_404(IncomingLetter, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.letter = self.letter
        form.instance.sender = self.request.user
        resp = super().form_valid(form)

        assignees = self.request.POST.getlist("assignees[]")
        for uid in assignees:
            if uid:
                DispositionAssignment.objects.get_or_create(
                    disposition=self.object,
                    assignee_id=uid
                )

        self.letter.status = "DISP"
        self.letter.save(update_fields=["status"])

        messages.success(self.request, "Disposisi dibuat dan penerima ditetapkan.")
        return resp

    def form_invalid(self, form):
        messages.error(self.request, "Form disposisi tidak valid.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """
        Saat invalid, kita perlu mengembalikan context yang sama dengan IncomingDetail:
        set 'object' = surat agar template incoming/detail.html tetap bisa render.
        """
        ctx = super().get_context_data(**kwargs)
        ctx["object"] = self.letter
        return ctx

    def get_success_url(self):
        return reverse_lazy("incoming_detail", args=[self.object.letter_id])


class FollowUpCreate(LoginRequiredMixin, CreateView):
    """
    Upload tindak lanjut (nota/balasan) dari halaman Detail Surat Masuk.
    """
    model = FollowUp
    form_class = FollowUpForm
    template_name = "incoming/detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.letter = get_object_or_404(IncomingLetter, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.letter = self.letter
        form.instance.author = self.request.user
        resp = super().form_valid(form)

        if self.request.POST.get("mark_done") == "1":
            self.letter.status = "DONE"
            self.letter.save(update_fields=["status"])
            messages.success(self.request, "Tindak lanjut diunggah & surat ditandai SELESAI.")
        else:
            messages.success(self.request, "Tindak lanjut berhasil diunggah.")
        return resp

    def form_invalid(self, form):
        messages.error(self.request, "Form tindak lanjut tidak valid.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["object"] = self.letter
        return ctx

    def get_success_url(self):
        return reverse_lazy("incoming_detail", args=[self.kwargs["pk"]])


# =========================
# KARTA SAI
# =========================

class OutgoingList(LoginRequiredMixin, ListView):
    model = OutgoingLetter
    paginate_by = 20
    ordering = ["-created_at"]
    template_name = "outgoing/list.html"


class OutgoingCreate(LoginRequiredMixin, CreateView):
    model = OutgoingLetter
    form_class = OutgoingLetterForm
    template_name = "outgoing/form.html"
    success_url = reverse_lazy("outgoing_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Draf surat keluar dibuat.")
        return super().form_valid(form)


class OutgoingUpdate(LoginRequiredMixin, UpdateView):
    model = OutgoingLetter
    form_class = OutgoingLetterForm
    template_name = "outgoing/form.html"
    success_url = reverse_lazy("outgoing_list")


class OutgoingDetail(LoginRequiredMixin, DetailView):
    model = OutgoingLetter
    template_name = "outgoing/detail.html"


class OutgoingSetStatus(LoginRequiredMixin, View):
    """
    Transisi status:
    REVIEW → APPROVED → FINAL (lock nomor via signal) → SENT → ARCH
    """
    def post(self, request, pk: int):
        letter = get_object_or_404(OutgoingLetter, pk=pk)
        target = request.POST.get("status")
        allowed = {"REVIEW", "APPROVED", "FINAL", "MANDA", "ARCH"}
        if target in allowed:
            letter.status = target
            letter.save(update_fields=["status"])  
            messages.success(request, f"Status diubah ke {target}.")
        else:
            messages.error(request, "Status tidak diperbolehkan.")
        return redirect("outgoing_detail", pk=pk)

@login_required
def ui_home(request):
    return redirect("ui_dashboard")

@login_required
def ui_dashboard(request):
    return redirect("/incoming/")


class UILogin(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("admin_home")

@login_required
def ui_dashboard(request):
    return redirect("admin_home")    