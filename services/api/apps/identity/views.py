from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


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
