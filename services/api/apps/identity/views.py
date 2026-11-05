from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import SecurityEvent


class CurrentAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        providers = user.provider_accounts.order_by("provider").values(
            "provider",
            "last_authenticated_at",
        )
        return Response({
            "id": str(user.pk),
            "status": user.status,
            "email_verified": getattr(request, "nexora_email_verified", False),
            "mfa_verified": getattr(request, "nexora_mfa_verified", False),
            "second_factor_type": getattr(request, "nexora_second_factor_type", ""),
            "created_at": user.created_at,
            "providers": list(providers),
        })


class SecurityEventListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = SecurityEvent.objects.filter(user=request.user).order_by("-occurred_at")[:50]
        return Response({
            "results": [
                {
                    "id": str(event.pk),
                    "event_type": event.event_type,
                    "occurred_at": event.occurred_at,
                    "provider": event.provider,
                    "source_ip": event.source_ip,
                    "user_agent": event.user_agent,
                }
                for event in events
            ],
        })


from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from .models import IdentitySession
from .security import record_security_event


class IdentitySessionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = IdentitySession.objects.filter(
            provider_account__user=request.user,
        ).select_related("provider_account").order_by("-last_seen_at")[:50]
        return Response({
            "results": [
                {
                    "id": str(session.pk),
                    "provider": session.provider_account.provider,
                    "authenticated_at": session.authenticated_at,
                    "created_at": session.created_at,
                    "last_seen_at": session.last_seen_at,
                    "revoked_at": session.revoked_at,
                    "is_active": session.revoked_at is None,
                    "is_current": str(session.pk) == str(getattr(request, "nexora_session_id", "")),
                    "mfa_verified": session.mfa_verified,
                    "second_factor_type": session.second_factor_type,
                    "source_ip": session.source_ip,
                    "user_agent": session.user_agent,
                }
                for session in sessions
            ],
        })


class IdentitySessionRevokeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "session_revoke"

    def post(self, request, session_id):
        session = get_object_or_404(
            IdentitySession.objects.select_related("provider_account"),
            pk=session_id,
            provider_account__user=request.user,
        )
        if session.revoked_at is not None:
            return Response({"status": "already_revoked"}, status=status.HTTP_200_OK)

        session.revoked_at = timezone.now()
        session.save(update_fields=("revoked_at",))
        record_security_event(
            user=request.user,
            actor=request.user,
            event_type=SecurityEvent.EventType.SESSION_REVOKED,
            request=request,
            provider=session.provider_account.provider,
        )
        return Response({"status": "revoked", "session_id": str(session.pk)})
