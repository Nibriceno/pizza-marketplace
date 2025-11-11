from .models import UserActionLog
from django.db import DatabaseError


def log_event(request=None, action="", page=None, product_id=None, extra_data=None, status="success", message=None):
    """
    Registra cualquier evento general del sistema (web, bot, checkout, webhook, etc.)

    Parámetros:
      - request: objeto HttpRequest (opcional)
      - action: descripción textual ("👀 Vio producto", "💳 Pago aprobado", etc.)
      - page: vista o módulo (ej: "product/detail", "cart/add", "cart/webhook")
      - product_id: ID del producto (opcional)
      - extra_data: diccionario JSON con detalles adicionales (precio, cantidad, orden, etc.)
      - status: "success" o "error"
      - message: texto de error o descripción extendida (opcional)
    """
    try:
        # 🧭 Obtener usuario si existe
        user = getattr(request, "user", None) if request else None
        is_auth = hasattr(user, "is_authenticated") and user.is_authenticated
        user_obj = user if is_auth else None
        user_name = getattr(user, "username", None) if is_auth else "Anónimo"

        # ⚙️ Preparar acción
        action_text = action
        if status == "error":
            action_text = f"❌ {action}"

        # ✅ Guardar log
        UserActionLog.objects.create(
            user=user_obj,
            user_name=user_name,
            action=action_text,
            page=page or "sistema",
            product_id=product_id,
            extra_data=extra_data or {},
        )

    except DatabaseError as e:
        print(f"⚠️ No se pudo guardar el log general: {e}")
        pass


def log_cart_event(request=None, product_id=None, action_type="action", status="success", message=None, extra_data=None):
    """
    Registra eventos específicos del carrito (web o bot), incluyendo errores funcionales.
    
    Parámetros:
      - request: objeto HttpRequest
      - product_id: ID del producto (opcional)
      - action_type: "add", "remove", "checkout", "view", etc.
      - status: "success" o "error"
      - message: texto extra para detallar errores o resultados
      - extra_data: diccionario opcional con datos complementarios (precio, cantidad, total, etc.)
    """
    try:
        user = getattr(request, "user", None) if request else None
        is_auth = hasattr(user, "is_authenticated") and user.is_authenticated
        user_obj = user if is_auth else None
        user_name = getattr(user, "username", None) if is_auth else "Anónimo"

        # 🧩 Mapeo de acciones predefinidas
        action_texts = {
            "add": "🛒 Agregó producto al carrito",
            "remove": "❌ Eliminó producto del carrito",
            "view": "👀 Vio producto",
            "checkout": "💳 Inició proceso de compra",
            "complete": "✅ Compra completada",
        }

        # 🧠 Determinar acción
        action = action_texts.get(action_type, "🧩 Acción desconocida")
        if status == "error":
            action = f"❌ ERROR FUNCIONAL: {message or action}"

        # ✅ Registrar log
        UserActionLog.objects.create(
            user=user_obj,
            user_name=user_name,
            action=action,
            page="cart/event",
            product_id=product_id,
            extra_data=extra_data or {},
        )

    except DatabaseError as e:
        print(f"⚠️ No se pudo guardar el log del carrito: {e}")
        pass
