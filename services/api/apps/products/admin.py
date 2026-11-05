from django.contrib import admin

from .models import (
    Entitlement,
    PlanFeature,
    Product,
    ProductMembership,
    ProductPlan,
    ProductSubscription,
)


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


@admin.register(ProductPlan)
class ProductPlanAdmin(admin.ModelAdmin):
    list_display = ("product", "key", "name", "tier", "price_minor", "currency", "is_active")
    list_filter = ("product", "tier", "is_active")
    search_fields = ("product__key", "key", "name")


@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    list_display = ("plan", "feature_key")
    list_filter = ("plan__product",)
    search_fields = ("plan__key", "feature_key")


@admin.register(ProductSubscription)
class ProductSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "plan", "status", "started_at", "current_period_end")
    list_filter = ("status", "product", "plan__tier")
    search_fields = ("user__id", "product__key", "plan__key")


@admin.register(Entitlement)
class EntitlementAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "feature_key", "status", "starts_at", "ends_at")
    list_filter = ("status", "product", "feature_key")
    search_fields = ("user__id", "product__key", "feature_key")
