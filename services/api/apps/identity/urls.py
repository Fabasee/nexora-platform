from django.urls import path

from .views import (
    CurrentAccountView,
    IdentitySessionListView,
    IdentitySessionRevokeView,
    SecurityEventListView,
)

urlpatterns = [
    path("me/", CurrentAccountView.as_view(), name="current-account"),
    path("security-events/", SecurityEventListView.as_view(), name="security-event-list"),
    path("sessions/", IdentitySessionListView.as_view(), name="identity-session-list"),
    path("sessions/<uuid:session_id>/revoke/", IdentitySessionRevokeView.as_view(), name="identity-session-revoke"),
]
