from django.conf.urls.static import static
from django.urls import path, include
from django.conf import settings
from django.contrib import admin
from django.db import router

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("login_and_register.urls")),
    path("api/", include("ai_recommender.urls")),
    path("api/", include("vendor.urls")),
    path("api/", include("order.urls")),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
