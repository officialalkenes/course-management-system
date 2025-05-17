from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from django.conf import settings


urlpatterns = [
    # Always available regardless of schema
    path("api/auth/", include("apps.user.urls")),
]

# Admin, tenant management, schema docs = public schema only
# You defer the decision to view-level or middleware-level behavior
public_only_urls = [
    path("admin/", admin.site.urls),
]

# Swagger only in debug
debug_only_urls = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

# Use middleware or per-app logic to handle schema separation at runtime
urlpatterns += public_only_urls

if settings.DEBUG:
    urlpatterns += debug_only_urls
