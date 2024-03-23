from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from train_station_service import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/train_station/", include("train_station.urls", namespace="train_station")),
    path("api/user/", include("user.urls", namespace="user")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/doc/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/doc/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("__debug__/", include("debug_toolbar.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
