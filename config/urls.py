"""URL configuration for printshopmgr."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("customers/", include("customers.urls")),
    path("jobs/", include("jobs.urls")),
    path("payments/", include("payments.urls")),
    path("documents/", include("documents.urls")),
    path("production/", include("production.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("track/", include("public.urls")),
    path("notifications/", include("notifications.urls")),
    path("", lambda request: redirect("dashboard:home")),  # root → dashboard
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
