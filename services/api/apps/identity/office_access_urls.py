from django.urls import path

from .office_access_views import (
    OfficeAccessProfileView, OfficeSecurityEventsView, OfficeSessionListView,
    OfficeSessionRevokeView, OfficeUserSessionsRevokeView,
)

urlpatterns = [
    path("me/", OfficeAccessProfileView.as_view(), name="office-access-profile"),
    path("security-events/", OfficeSecurityEventsView.as_view(), name="office-security-events"),
    path("sessions/", OfficeSessionListView.as_view(), name="office-session-list"),
    path("sessions/<uuid:session_id>/revoke/", OfficeSessionRevokeView.as_view(), name="office-session-revoke"),
    path("users/<uuid:user_id>/sessions/revoke/", OfficeUserSessionsRevokeView.as_view(), name="office-user-sessions-revoke"),
]
