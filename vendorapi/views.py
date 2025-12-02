from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from vendorapi.auth import APIKeyAuth
from vendorapi.serializers import OrderSerializer
from order.models import Order

# --------------------------------------
#     API REST DEL POS EXTERNO
# --------------------------------------

# ➤ Obtener todas las órdenes del vendor
@api_view(["GET"])
@authentication_classes([APIKeyAuth])
@permission_classes([])
def vendor_orders(request):
    vendor = request.auth  # el vendor autenticado por API Key
    orders = Order.objects.filter(vendors=vendor).order_by("-created_at")
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


# ➤ Obtener detalle de una orden
@api_view(["GET"])
@authentication_classes([APIKeyAuth])
@permission_classes([])
def vendor_order_detail(request, order_id):
    vendor = request.auth
    order = get_object_or_404(Order, id=order_id, vendors=vendor)
    serializer = OrderSerializer(order)
    return Response(serializer.data)


# ➤ Cambiar estado (para POS externo)
@api_view(["POST"])
@authentication_classes([APIKeyAuth])
@permission_classes([])
def vendor_update_status(request, order_id):
    vendor = request.auth
    new_status = request.data.get("status")

    valid_states = ["accepted", "rejected", "preparing", "ready", "delivered"]

    if new_status not in valid_states:
        return Response({"detail": "Invalid status"}, status=400)

    order = get_object_or_404(Order, id=order_id, vendors=vendor)

    # cambiar estado
    order.status = new_status
    order.save()

    return Response({"success": True, "new_status": new_status})
