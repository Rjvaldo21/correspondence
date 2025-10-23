from django.urls import path
from .admin_views import (
    AdminHome,  # atau AdminDashboard
    AdminIncomingList, AdminOutgoingList,
    AdminIncomingCreate, AdminIncomingUpdate, AdminIncomingDetail,
    AdminDispositionCreate, AdminFollowUpCreate,
    AdminOutgoingCreate, AdminOutgoingUpdate, AdminOutgoingDetail,
    AdminOutgoingSetStatus,   # ← penting
)

urlpatterns = [
    path("", AdminHome.as_view(), name="admin_home"),

    # Incoming
    path("incoming/", AdminIncomingList.as_view(), name="admin_incoming_list"),
    path("incoming/new/", AdminIncomingCreate.as_view(), name="admin_incoming_create"),
    path("incoming/<int:pk>/", AdminIncomingDetail.as_view(), name="admin_incoming_detail"),
    path("incoming/<int:pk>/edit/", AdminIncomingUpdate.as_view(), name="admin_incoming_update"),
    path("incoming/<int:pk>/disposition/", AdminDispositionCreate.as_view(), name="admin_disposition_create"),
    path("incoming/<int:pk>/followup/", AdminFollowUpCreate.as_view(), name="admin_followup_create"),

    # Outgoing
    path("outgoing/", AdminOutgoingList.as_view(), name="admin_outgoing_list"),
    path("outgoing/new/", AdminOutgoingCreate.as_view(), name="admin_outgoing_create"),
    path("outgoing/<int:pk>/", AdminOutgoingDetail.as_view(), name="admin_outgoing_detail"),
    path("outgoing/<int:pk>/edit/", AdminOutgoingUpdate.as_view(), name="admin_outgoing_update"),

    # 🔽 Tambahkan ini
    path(
        "outgoing/<int:pk>/set-status/",
        AdminOutgoingSetStatus.as_view(),
        name="admin_outgoing_set_status",
    ),
]
