from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.models import SecurityEvent
from apps.identity.office_access import OfficeAccessPermission, get_office_permissions, get_office_roles


class OfficeAccessPermissionMixin:
    permission_classes = (OfficeAccessPermission,)


class OfficeAccessProfileView(OfficeAccessPermissionMixin, APIView):
    office_permission = "access.view_self"

    def get(self, request):
        return Response({
            "user_id": str(request.user.pk),
            "roles": get_office_roles(request.user),
            "permissions": sorted(get_office_permissions(request.user)),
        })


class OfficeSecurityEventsView(OfficeAccessPermissionMixin, APIView):
    office_permission = "security.view"
    allowed_types = SecurityEvent.EventType.values

    def get(self, request):
        queryset = SecurityEvent.objects.select_related("user").order_by("-occurred_at", "-id")
        event_type = request.query_params.get("event_type", "").strip()
        if event_type:
            if event_type not in self.allowed_types:
                return Response({"detail": "Invalid event_type filter."}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(event_type=event_type)
        user_id = request.query_params.get("user_id", "").strip()
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        try:
            limit = min(max(int(request.query_params.get("limit", 50)), 1), 100)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except (TypeError, ValueError):
            return Response({"detail": "limit and offset must be integers."}, status=status.HTTP_400_BAD_REQUEST)
        total = queryset.count()
        return Response({
            "count": total,
            "limit": limit,
            "offset": offset,
            "results": [{
                "id": str(event.pk),
                "user_id": str(event.user_id),
                "event_type": event.event_type,
                "occurred_at": event.occurred_at.isoformat(),
                "provider": event.provider,
                "source_ip": event.source_ip,
                "user_agent": event.user_agent,
                "request_id": event.request_id,
            } for event in queryset[offset:offset + limit]],
        })
