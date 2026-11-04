from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
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
