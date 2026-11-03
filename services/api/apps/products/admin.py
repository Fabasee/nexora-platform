from django.contrib import admin

from .models import Entitlement, Product, ProductMembership


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("key", "name")


@admin.register(ProductMembership)
class ProductMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "status", "joined_at")
    list_filter = ("status", "product")
    search_fields = ("user__id", "product__key")


@admin.register(Entitlement)
class EntitlementAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "feature_key", "status", "starts_at", "ends_at")
    list_filter = ("status", "product", "feature_key")
    search_fields = ("user__id", "product__key", "feature_key")
