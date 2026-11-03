from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/products/", include("apps.products.urls")),
    path("api/v1/account/", include("apps.identity.urls")),
]
