from django.contrib import admin

from .models import IdentityProviderAccount, NexoraUser, SecurityEvent


@admin.register(NexoraUser)
class NexoraUserAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("id",)
    readonly_fields = ("id", "created_at", "updated_at", "last_login")


@admin.register(IdentityProviderAccount)
class IdentityProviderAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "provider", "last_authenticated_at")
    list_filter = ("provider",)
    search_fields = ("user__id",)
    readonly_fields = ("id", "created_at", "updated_at", "last_authenticated_at", "provider_subject")


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "event_type", "user", "provider", "source_ip")
    list_filter = ("event_type", "provider", "occurred_at")
    search_fields = ("user__id", "request_id")
    readonly_fields = (
        "id", "user", "event_type", "occurred_at", "provider",
        "source_ip", "user_agent", "request_id", "dedupe_key",
    )

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
