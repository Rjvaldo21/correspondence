from django.urls import path
from . import views
from .admin_views import (
    AdminHome,                  
    AdminIncomingList,
    AdminIncomingCreate,
    AdminIncomingUpdate,
    AdminOutgoingList,
    AdminOutgoingCreate,
    AdminOutgoingUpdate,
    AdminOutgoingDetail,
    AdminOutgoingSetStatus,
    AdminFollowUpCreate,
)

urlpatterns = [
    # DASHBOARD ADMIN PERSURATAN
    path("", AdminHome.as_view(), name="admin_home"),

    # ========== INCOMING (Karta Tama) ==========
    path("incoming/", AdminIncomingList.as_view(), name="admin_incoming_list"),
    path("incoming/new/", AdminIncomingCreate.as_view(), name="admin_incoming_create"),

    # Detail surat masuk (pakai view function dengan Despacho + tugas)
    path("incoming/<int:pk>/", views.incoming_detail_view, name="admin_incoming_detail"),

    path("incoming/<int:pk>/edit/", AdminIncomingUpdate.as_view(), name="admin_incoming_update"),
    path("incoming/<int:pk>/followup/", AdminFollowUpCreate.as_view(), name="admin_followup_create"),

    # ========== OUTGOING (Karta Sai) ==========
    path("outgoing/", AdminOutgoingList.as_view(), name="admin_outgoing_list"),

    # 🔹 INI YANG DICARI TEMPLATE: 'admin_outgoing_create'
    path("outgoing/new/", AdminOutgoingCreate.as_view(), name="admin_outgoing_create"),

    path("outgoing/<int:pk>/", AdminOutgoingDetail.as_view(), name="admin_outgoing_detail"),
    path("outgoing/<int:pk>/edit/", AdminOutgoingUpdate.as_view(), name="admin_outgoing_update"),
    path(
        "outgoing/<int:pk>/set-status/",
        AdminOutgoingSetStatus.as_view(),
        name="admin_outgoing_set_status",
    ),
]
