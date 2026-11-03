from django.urls import path

from .views import CurrentAccountView

urlpatterns = [
    path("me/", CurrentAccountView.as_view(), name="current-account"),
]
