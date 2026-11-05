from django.contrib import admin

from .models import (
    Entitlement,
    PlanFeature,
    Product,
    ProductMembership,
    ProductPlan,
    ProductPortfolioEntry,
    PortfolioAuditEvent,
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


from .portfolio_audit import save_portfolio_entry


@admin.register(ProductPortfolioEntry)
class ProductPortfolioEntryAdmin(admin.ModelAdmin):
    list_display = (
        "name", "key", "entry_type", "parent", "lifecycle_status",
        "decision_status", "priority", "delivery_model",
    )
    list_filter = (
        "entry_type", "lifecycle_status", "decision_status",
        "priority", "delivery_model", "category",
    )
    search_fields = ("key", "name", "description", "category", "parent__name")
    autocomplete_fields = ("parent", "activation_product")
    list_select_related = ("parent", "activation_product")
    ordering = ("sort_order", "name")

    def save_model(self, request, obj, form, change):
        saved, _ = save_portfolio_entry(
            entry=obj,
            source=PortfolioAuditEvent.Source.ADMIN,
            actor=request.user,
        )
        obj.pk = saved.pk

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PortfolioAuditEvent)
class PortfolioAuditEventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "entry_key", "action", "source", "actor_label")
    list_filter = ("action", "source", "occurred_at")
    search_fields = ("entry_key", "entry_name", "actor_label")
    readonly_fields = (
        "id", "entry", "entry_key", "entry_name", "action", "source",
        "actor", "actor_label", "changes", "occurred_at",
    )
    ordering = ("-occurred_at",)
    date_hierarchy = "occurred_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
