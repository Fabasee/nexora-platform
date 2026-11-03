from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import ProductAccessService


class AccessibleProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = ProductAccessService.list_accessible_products(request.user)
        return Response({
            "results": [
                {
                    "key": product.key,
                    "name": product.name,
                    "description": product.description,
                }
                for product in products
            ],
        })
