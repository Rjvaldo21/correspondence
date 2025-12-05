from django.views.generic import TemplateView, RedirectView, View
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib import messages

from .models import IncomingLetter, OutgoingLetter
from .views import (
    IncomingList, IncomingCreate, IncomingUpdate, IncomingDetail,
    # DispositionCreate,   # ⬅️ JANGAN DIIMPORT LAGI
    FollowUpCreate,
    OutgoingList, OutgoingCreate, OutgoingUpdate, OutgoingDetail,
)

# ========== DASHBOARD ==========
class AdminDashboard(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.utils import timezone
        from .models import IncomingLetter, OutgoingLetter
        today = timezone.localdate()
        ctx["stats"] = {
            "incoming_today": IncomingLetter.objects.filter(created_at__date=today).count(),
            "incoming_in_progress": IncomingLetter.objects.filter(status__in=["DISP", "PROG"]).count(),
            "incoming_done": IncomingLetter.objects.filter(status="DONE").count(),
            "incoming_total": IncomingLetter.objects.count(),
            "outgoing_draft": OutgoingLetter.objects.filter(status="DRAFT").count(),
            "outgoing_review": OutgoingLetter.objects.filter(status="REVIEW").count(),
            "outgoing_final": OutgoingLetter.objects.filter(status="FINAL").count(),
            "outgoing_sent": OutgoingLetter.objects.filter(status="MANDA").count(),
            "outgoing_total": OutgoingLetter.objects.count(),
        }
        ctx["recent_incoming"] = IncomingLetter.objects.order_by("-created_at")[:10]
        ctx["recent_outgoing"] = OutgoingLetter.objects.order_by("-created_at")[:10]
        return ctx

AdminHome = AdminDashboard


# ========== LIST REDIRECT KE DASHBOARD ==========
class AdminIncomingList(RedirectView):
    pattern_name = "admin_home"
    permanent = False

class AdminOutgoingList(RedirectView):
    pattern_name = "admin_home"
    permanent = False


# ========== FORM & DETAIL ==========
class AdminIncomingCreate(IncomingCreate):
    template_name = "adminui/incoming/form.html"
    def get_template_names(self):
        return ["adminui/incoming/form.html", "incoming/form.html"]


class AdminIncomingUpdate(IncomingUpdate):
    template_name = "incoming/form.html"
    def get_template_names(self):
        return ["incoming/form.html", "admin/incoming/form.html"]
    def get_success_url(self):
        return reverse_lazy("admin_home")

class AdminIncomingDetail(IncomingDetail):
    template_name = "incoming/detail.html"
    def get_template_names(self):
        return ["incoming/detail.html", "admin/incoming/detail.html"]


# class AdminDispositionCreate(DispositionCreate):
#     template_name = "incoming/detail.html"
#     def get_template_names(self):
#         return ["incoming/detail.html", "admin/incoming/detail.html"]
#     def get_success_url(self):
#         return reverse_lazy("admin_home")

class AdminFollowUpCreate(FollowUpCreate):
    template_name = "incoming/detail.html"
    def get_template_names(self):
        return ["incoming/detail.html", "admin/incoming/detail.html"]
    def get_success_url(self):
        return reverse_lazy("admin_home")


class AdminOutgoingCreate(OutgoingCreate):
    template_name = "outgoing/form.html"
    success_url = reverse_lazy("admin_home")
    def get_template_names(self):
        return ["outgoing/form.html", "admin/outgoing/form.html"]

class AdminOutgoingUpdate(OutgoingUpdate):
    template_name = "outgoing/form.html"
    success_url = reverse_lazy("admin_home")
    def get_template_names(self):
        return ["outgoing/form.html", "admin/outgoing/form.html"]

class AdminOutgoingDetail(OutgoingDetail):
    template_name = "outgoing/detail.html"
    def get_template_names(self):
        return ["outgoing/detail.html", "admin/outgoing/detail.html"]


class AdminOutgoingSetStatus(View):
    def post(self, request, pk):
        resp = OutgoingSetStatus.as_view()(request, pk=pk)
        messages.success(request, "Status karta sai atualiza ona.")
        return resp

