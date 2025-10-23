from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views  # <-- sudah ada

urlpatterns = [
    path("admin/persuratan/", include("core.admin_urls")),
    path("admin/", admin.site.urls),

    path("", include("core.urls")),

    # Login standar (opsional, arahkan ke tempat sama)
    path("login/", core_views.UILogin.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", core_views.ui_logout if hasattr(core_views, "ui_logout") else
         __import__("django.contrib.auth.views", fromlist=["LogoutView"]).LogoutView.as_view(), name="logout"),

    # Login UI terpisah
    path("ui/login/", core_views.UILogin.as_view(), name="ui_login"),
    path("ui/logout/", __import__("django.contrib.auth.views", fromlist=["LogoutView"]).LogoutView.as_view(), name="ui_logout"),

    # Home & dashboard
    path("ui/", core_views.ui_home, name="ui_home"),
    path("dashboard/", core_views.ui_dashboard, name="ui_dashboard"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)