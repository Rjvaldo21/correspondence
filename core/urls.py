from django.urls import path
from .views_public import verify_document
from . import views

urlpatterns = [
    path("", views.IncomingList.as_view(), name="home"),  # halaman awal
    path("verify/<path:code>/", verify_document, name="verify_document"),

    # Surat Masuk
    path("incoming/", views.IncomingList.as_view(), name="incoming_list"),
    path("incoming/new/", views.IncomingCreate.as_view(), name="incoming_create"),
    path("incoming/<int:pk>/", views.IncomingDetail.as_view(), name="incoming_detail"),
    path("incoming/<int:pk>/edit/", views.IncomingUpdate.as_view(), name="incoming_update"),
    path("incoming/<int:pk>/disposition/new/", views.DispositionCreate.as_view(), name="disposition_create"),
    path("incoming/<int:pk>/followup/new/", views.FollowUpCreate.as_view(), name="followup_create"),

    # Surat Keluar
    path("outgoing/", views.OutgoingList.as_view(), name="outgoing_list"),
    path("outgoing/new/", views.OutgoingCreate.as_view(), name="outgoing_create"),
    path("outgoing/<int:pk>/", views.OutgoingDetail.as_view(), name="outgoing_detail"),
    path("outgoing/<int:pk>/edit/", views.OutgoingUpdate.as_view(), name="outgoing_update"),
    path("outgoing/<int:pk>/status/", views.OutgoingSetStatus.as_view(), name="outgoing_set_status"),
]