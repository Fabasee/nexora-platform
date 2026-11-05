from django.urls import path

from .views import (
    AccessibleProductsView, ProductActivationView, ProductCatalogView, ProductSubscriptionView,
)

urlpatterns = [
    path("catalog/", ProductCatalogView.as_view(), name="product-catalog"),
    path("", AccessibleProductsView.as_view(), name="accessible-products"),
    path("<slug:product_key>/activate/", ProductActivationView.as_view(), name="product-activate"),
    path("<slug:product_key>/subscription/", ProductSubscriptionView.as_view(), name="product-subscription"),
]
