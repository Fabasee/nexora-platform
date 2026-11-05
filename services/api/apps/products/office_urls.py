from django.urls import path

from .office_views import (
    OfficePortfolioDetailView,
    OfficePortfolioListView,
    OfficePortfolioSummaryView,
)

urlpatterns = [
    path("summary/", OfficePortfolioSummaryView.as_view(), name="office-portfolio-summary"),
    path("portfolio/", OfficePortfolioListView.as_view(), name="office-portfolio-list"),
    path("portfolio/<slug:key>/", OfficePortfolioDetailView.as_view(), name="office-portfolio-detail"),
]
