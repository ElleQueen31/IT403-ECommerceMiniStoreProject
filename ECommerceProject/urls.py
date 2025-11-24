from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # ✅ Django auth (login, logout, password reset)
    path("account/", include("django.contrib.auth.urls")),

    # MiniStore app
    path("", include("MiniStore.urls")),

]

# ✅ This serves media files (images) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)