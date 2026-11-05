from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.models import IdentitySession, NexoraUser, SecurityEvent
from apps.identity.security import record_security_event
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
        queryset = SecurityEvent.objects.select_related("user", "actor").order_by("-occurred_at", "-id")
        event_type = request.query_params.get("event_type", "").strip()
        if event_type:
            if event_type not in self.allowed_types:
                return Response({"detail": "Invalid event_type filter."}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(event_type=event_type)
        user_id = request.query_params.get("user_id", "").strip()
        if user_id:
            try:
                user_id = UUID(user_id)
            except (TypeError, ValueError, AttributeError):
                return Response({"detail": "user_id must be a valid UUID."}, status=status.HTTP_400_BAD_REQUEST)
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
                "actor_id": str(event.actor_id) if event.actor_id else None,
                "event_type": event.event_type,
                "occurred_at": event.occurred_at.isoformat(),
                "provider": event.provider,
                "source_ip": event.source_ip,
                "user_agent": event.user_agent,
                "request_id": event.request_id,
            } for event in queryset[offset:offset + limit]],
        })


class OfficeSessionListView(OfficeAccessPermissionMixin, APIView):
    office_permission = "sessions.manage"

    def get(self, request):
        queryset = IdentitySession.objects.select_related(
            "provider_account", "provider_account__user"
        ).order_by("-last_seen_at", "-id")
        user_id = request.query_params.get("user_id", "").strip()
        if user_id:
            try:
                user_id = UUID(user_id)
            except (TypeError, ValueError, AttributeError):
                return Response({"detail": "user_id must be a valid UUID."}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(provider_account__user_id=user_id)
        active = request.query_params.get("active", "").strip().lower()
        if active in {"true", "1"}:
            queryset = queryset.filter(revoked_at__isnull=True)
        elif active in {"false", "0"}:
            queryset = queryset.filter(revoked_at__isnull=False)
        elif active:
            return Response({"detail": "active must be true or false."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            limit = min(max(int(request.query_params.get("limit", 50)), 1), 100)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except (TypeError, ValueError):
            return Response({"detail": "limit and offset must be integers."}, status=status.HTTP_400_BAD_REQUEST)
        total = queryset.count()
        results = [{
            "id": str(session.pk),
            "user_id": str(session.provider_account.user_id),
            "provider": session.provider_account.provider,
            "authenticated_at": session.authenticated_at.isoformat(),
            "last_seen_at": session.last_seen_at.isoformat(),
            "revoked_at": session.revoked_at.isoformat() if session.revoked_at else None,
            "is_active": session.revoked_at is None,
            "mfa_verified": session.mfa_verified,
            "second_factor_type": session.second_factor_type,
            "source_ip": session.source_ip,
            "user_agent": session.user_agent,
        } for session in queryset[offset:offset + limit]]
        return Response({"count": total, "limit": limit, "offset": offset, "results": results})


class OfficeSessionRevokeView(OfficeAccessPermissionMixin, APIView):
    office_permission = "sessions.manage"

    def post(self, request, session_id):
        session = get_object_or_404(
            IdentitySession.objects.select_related("provider_account"), pk=session_id
        )
        if str(session.pk) == str(getattr(request, "nexora_session_id", "")):
            return Response(
                {"detail": "The current operator session cannot be revoked from this endpoint."},
                status=status.HTTP_409_CONFLICT,
            )
        if session.revoked_at is not None:
            return Response({"status": "already_revoked", "session_id": str(session.pk)})
        now = timezone.now()
        with transaction.atomic():
            updated = IdentitySession.objects.filter(pk=session.pk, revoked_at__isnull=True).update(revoked_at=now)
            if updated:
                record_security_event(
                    user=session.provider_account.user, actor=request.user,
                    event_type=SecurityEvent.EventType.SESSION_REVOKED, request=request,
                    provider=session.provider_account.provider,
                )
        if not updated:
            return Response({"status": "already_revoked", "session_id": str(session.pk)})
        return Response({"status": "revoked", "session_id": str(session.pk)})


class OfficeUserSessionsRevokeView(OfficeAccessPermissionMixin, APIView):
    office_permission = "sessions.manage"

    def post(self, request, user_id):
        user = get_object_or_404(NexoraUser, pk=user_id)
        sessions = IdentitySession.objects.filter(
            provider_account__user=user, revoked_at__isnull=True
        ).exclude(pk=getattr(request, "nexora_session_id", None))
        now = timezone.now()
        revoked_ids = []
        with transaction.atomic():
            locked = list(sessions.select_for_update().select_related("provider_account"))
            for session in locked:
                session.revoked_at = now
                session.save(update_fields=("revoked_at",))
                record_security_event(
                    user=user, actor=request.user,
                    event_type=SecurityEvent.EventType.SESSION_REVOKED, request=request,
                    provider=session.provider_account.provider,
                )
                revoked_ids.append(str(session.pk))
        return Response({
            "status": "revoked",
            "user_id": str(user.pk),
            "revoked_count": len(revoked_ids),
            "session_ids": revoked_ids,
        })
