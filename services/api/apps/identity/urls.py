from django.urls import path

from .views import CurrentAccountView, SecurityEventListView

urlpatterns = [
    path("me/", CurrentAccountView.as_view(), name="current-account"),
    path("security-events/", SecurityEventListView.as_view(), name="security-event-list"),
]
