from django.db.models import Count, Prefetch, Q
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.office_access import OfficeAccessPermission

from .models import PortfolioAuditEvent, ProductPortfolioEntry
from .office_serializers import (OfficePortfolioAuditEventSerializer, PortfolioEntryDetailSerializer, PortfolioEntrySerializer)


class InternalOfficePermissionMixin:
    """Require verified staff identity and a least-privilege Office role."""

    permission_classes = (OfficeAccessPermission,)


class OfficePortfolioSummaryView(InternalOfficePermissionMixin, APIView):
    office_permission = "portfolio.view"
    def get(self, request):
        queryset = ProductPortfolioEntry.objects.all()
        return Response({
            "total_entries": queryset.count(),
            "applications": queryset.filter(
                entry_type=ProductPortfolioEntry.EntryType.APPLICATION
            ).count(),
            "modules": queryset.filter(
                entry_type=ProductPortfolioEntry.EntryType.MODULE
            ).count(),
            "platform_services": queryset.filter(
                entry_type=ProductPortfolioEntry.EntryType.PLATFORM_SERVICE
            ).count(),
            "by_lifecycle_status": {
                item["lifecycle_status"]: item["total"]
                for item in queryset.values("lifecycle_status").annotate(total=Count("id"))
            },
            "by_decision_status": {
                item["decision_status"]: item["total"]
                for item in queryset.values("decision_status").annotate(total=Count("id"))
            },
            "by_priority": {
                item["priority"]: item["total"]
                for item in queryset.values("priority").annotate(total=Count("id"))
            },
        })


class OfficePortfolioListView(InternalOfficePermissionMixin, APIView):
    office_permission = "portfolio.view"
    filter_fields = {
        "entry_type": ProductPortfolioEntry.EntryType.values,
        "lifecycle_status": ProductPortfolioEntry.LifecycleStatus.values,
        "decision_status": ProductPortfolioEntry.DecisionStatus.values,
        "priority": ProductPortfolioEntry.Priority.values,
        "delivery_model": ProductPortfolioEntry.DeliveryModel.values,
    }

    def get(self, request):
        queryset = ProductPortfolioEntry.objects.select_related(
            "parent", "activation_product"
        ).annotate(module_count=Count("modules", distinct=True))

        for field, allowed_values in self.filter_fields.items():
            value = request.query_params.get(field)
            if value:
                if value not in allowed_values:
                    return Response(
                        {"detail": f"Invalid {field} filter.", "allowed": list(allowed_values)},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                queryset = queryset.filter(**{field: value})

        parent_key = request.query_params.get("parent")
        if parent_key:
            queryset = queryset.filter(parent__key=parent_key)

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(key__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
            )

        try:
            limit = min(max(int(request.query_params.get("limit", 50)), 1), 100)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except (TypeError, ValueError):
            return Response(
                {"detail": "limit and offset must be integers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total = queryset.count()
        page = queryset.order_by("sort_order", "name")[offset:offset + limit]
        return Response({
            "count": total,
            "limit": limit,
            "offset": offset,
            "results": PortfolioEntrySerializer(page, many=True).data,
        })


class OfficePortfolioDetailView(InternalOfficePermissionMixin, APIView):
    office_permission = "portfolio.view"
    def get(self, request, key):
        entry = ProductPortfolioEntry.objects.select_related(
            "parent", "activation_product"
        ).prefetch_related(
            Prefetch("modules", queryset=ProductPortfolioEntry.objects.order_by("sort_order", "name"))
        ).annotate(module_count=Count("modules", distinct=True)).filter(key=key).first()
        if entry is None:
            raise Http404("Portfolio entry not found.")
        return Response(PortfolioEntryDetailSerializer(entry).data)



class OfficePortfolioAuditView(InternalOfficePermissionMixin, APIView):
    office_permission = "audit.view"
    def get(self, request):
        queryset = PortfolioAuditEvent.objects.select_related("actor")
        entry_key = request.query_params.get("entry_key", "").strip()
        action = request.query_params.get("action", "").strip()
        source = request.query_params.get("source", "").strip()
        if entry_key:
            queryset = queryset.filter(entry_key=entry_key)
        if action:
            if action not in PortfolioAuditEvent.Action.values:
                return Response({"detail": "Invalid action filter."}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(action=action)
        if source:
            if source not in PortfolioAuditEvent.Source.values:
                return Response({"detail": "Invalid source filter."}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(source=source)
        try:
            limit = min(max(int(request.query_params.get("limit", 50)), 1), 100)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except (TypeError, ValueError):
            return Response(
                {"detail": "limit and offset must be integers."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        total = queryset.count()
        page = queryset.order_by("-occurred_at", "-id")[offset:offset + limit]
        return Response({
            "count": total,
            "limit": limit,
            "offset": offset,
            "results": OfficePortfolioAuditEventSerializer(page, many=True).data,
        })
