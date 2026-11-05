from django.urls import path

from .office_access_views import OfficeAccessProfileView, OfficeSecurityEventsView

urlpatterns = [
    path("me/", OfficeAccessProfileView.as_view(), name="office-access-profile"),
    path("security-events/", OfficeSecurityEventsView.as_view(), name="office-security-events"),
]
