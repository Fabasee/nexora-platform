from django.urls import path

from .views import AccessibleProductsView

urlpatterns = [
    path("", AccessibleProductsView.as_view(), name="accessible-products"),
]
